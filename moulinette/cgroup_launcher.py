"""Lancement expérimental d'un correcteur dans un scope systemd utilisateur.

Code de confiance uniquement. Aucun fallback en cas de contrôle indéterminé.
"""
import os
import secrets
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import threading
from contextlib import contextmanager
from pathlib import Path
from .cgroup_gate import CgroupGateUnavailable, verify_current_scope
from .scope_protocol import ScopeProtocolError, receive_object, send_object
from .exercise_catalog import EXERCISES, canonical_exercise


def _events(path):
    try:
        rows = [line.split() for line in (path / 'cgroup.events').read_text(encoding='ascii').splitlines()]
        vals = [line[1] for line in rows if len(line) == 2 and line[0] == 'populated']
        if len(vals) != 1 or vals[0] not in ('0', '1'):
            return None
        return int(vals[0])
    except FileNotFoundError:
        # Le fichier manquant ne prouve pas à lui seul que le scope a disparu.
        # Ne considérer le groupe absent que si son répertoire a disparu et
        # que son parent reste accessible. Toute autre situation est ambiguë.
        try:
            path.lstat()
        except FileNotFoundError:
            try:
                if not path.parent.is_dir():
                    return None
            except OSError:
                return None
            return 0
        except OSError:
            return None
        return None
    except (OSError, UnicodeError):
        return None


def _stop(systemctl, scope, env):
    try:
        subprocess.run([systemctl, '--user', 'stop', scope], stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _accept_or_exit(listener, proc, timeout=15):
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ScopeProtocolError('Délai de démarrage du superviseur dépassé.')
        readable, _, _ = select.select([listener], [], [], min(remaining, 0.2))
        if readable:
            return listener.accept()
        if proc.poll() is not None:
            raise ScopeProtocolError('Le lanceur systemd s’est arrêté avant la connexion du superviseur.')


@contextmanager
def _termination_signals():
    """Convertir SIGTERM/SIGHUP en interruption nettoyable sur le thread principal.

    SIGKILL ne peut pas être capturé. La restauration ne couvre que la durée du
    lancement ; les signaux ne sont pas installés si appelé depuis un thread.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = {}
    interrupted = False
    def interrupt(signum, frame):
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt
    try:
        for signum in (signal.SIGTERM, signal.SIGHUP):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, interrupt)
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def _required_passes(exercise):
    """Contrôles minimaux pour un rapport favorable, selon le catalogue interne."""
    ident = canonical_exercise(exercise)
    if ident is None:
        raise ScopeProtocolError('Exercice non pris en charge.')
    names = {'Fichiers attendus', 'Compilation', 'Prototype et liaison'}
    if 'project' not in EXERCISES[ident] or (EXERCISES[ident]['project'].get('style_files') or EXERCISES[ident]['project'].get('style_all_sources')):
        names.add('Norminette adaptée')
    names.update('Test ' + row[0] for row in EXERCISES[ident]['cases'])
    return names


def _validate_favorable_checks(exercise, checks):
    required=_required_passes(exercise)
    for name in required:
        matching=[c for c in checks if c['name']==name]
        if len(matching)!=1 or matching[0]['status']!='pass':
            raise ScopeProtocolError('Rapport favorable sans contrôles obligatoires uniques.')
    if any(c['status']=='pass' and c['name'] not in required for c in checks):
        raise ScopeProtocolError('Contrôle favorable inconnu dans le rapport.')
    allowed_info={'Fonctions externes','Adaptation compilation','Recompilation','Convention de test','Sortie stderr','Limites','Norminette adaptée','Récursivité (indicative)','Structure (indicative)','Sanitizer (optionnel)'}
    info_names=[c['name'] for c in checks if c['status']=='info']
    if any(name not in allowed_info for name in info_names):
        raise ScopeProtocolError('Information inconnue dans le rapport favorable.')
    if any(info_names.count(name)>1 for name in allowed_info if name!='Sortie stderr'):
        raise ScopeProtocolError('Information unique répétée dans le rapport favorable.')
    external=[c for c in checks if c['name']=='Fonctions externes']
    if len(external)!=1 or external[0]['status']!='info':
        raise ScopeProtocolError('Rapport favorable sans information unique sur les fonctions externes.')


def _peer_identity(conn):
    try:
        raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('iII'))
        pid, uid, gid = struct.unpack('iII', raw)
    except (OSError, ValueError, struct.error, AttributeError) as exc:
        raise ScopeProtocolError('Identité du pair indisponible.') from exc
    if pid <= 0 or uid != os.getuid():
        raise ScopeProtocolError('Identité du pair incohérente.')
    return pid


def _wait_unpopulated(base, timeout=1.0):
    deadline = time.monotonic() + timeout
    while True:
        value = _events(base)
        if value == 0: return True
        if value is None or time.monotonic() >= deadline: return False
        time.sleep(min(0.025, max(0, deadline - time.monotonic())))


def launch(path, exercise):
    run = shutil.which('systemd-run')
    systemctl = shutil.which('systemctl')
    if not run or not systemctl:
        return None, 'systemd-run ou systemctl introuvable ; aucune correction lancée.'
    scope = 'moulinette-' + secrets.token_hex(16) + '.scope'
    env = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'PATH', 'LANG') if key in os.environ}
    env['LC_ALL'] = 'C'
    proc = None
    base = None
    report = None
    error = None
    with _termination_signals(), tempfile.TemporaryDirectory(prefix='mlcg-') as folder:
        sockpath = str(Path(folder) / 'control.sock')
        if len(os.fsencode(sockpath)) > 100:
            return None, 'Chemin du canal local trop long ; aucune correction lancée.'
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(sockpath)
            listener.listen(1)
            listener.settimeout(15)
            cmd = [run, '--user', '--scope', '--quiet', '--unit=' + scope,
                   '-p', 'TasksMax=32', '-p', 'MemoryMax=512M', '-p', 'MemorySwapMax=0',
                   '-p', 'CPUQuota=100%', '--', sys.executable, '-m', 'moulinette.cgroup_worker',
                   '--socket', sockpath, '--scope', scope]
            try:
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, start_new_session=True)
                conn, _ = _accept_or_exit(listener, proc)
                with conn:
                    conn.settimeout(15)
                    peer_pid = _peer_identity(conn)
                    ready = receive_object(conn)
                    if ready.get('phase') == 'unavailable':
                        raise ScopeProtocolError(str(ready.get('message', 'Vérification du scope impossible.'))[:500])
                    if (set(ready) != {'phase', 'pid', 'scope'} or ready['phase'] != 'ready'
                        or ready['scope'] != scope or type(ready['pid']) is not int or ready['pid'] <= 0):
                        raise ScopeProtocolError('Réponse initiale inattendue.')
                    pid = ready['pid']
                    if pid != peer_pid:
                        raise ScopeProtocolError('PID déclaré différent du pair du socket.')
                    state = verify_current_scope(scope, proc_cgroup=Path('/proc') / str(pid) / 'cgroup', pid=pid, swap_max=0)
                    base = Path('/sys/fs/cgroup') / state['group'].lstrip('/')
                    if _events(base) != 1:
                        raise CgroupGateUnavailable('État du scope absent ou non actif.')
                    send_object(conn, {'action': 'run', 'path': str(path), 'exercise': exercise})
                    # 110 s projet + 90 s Norminette + marge de 30 s,
                    # bornés pour l'ensemble du message même s'il arrive fragmenté.
                    answer = receive_object(conn, deadline=time.monotonic()+230)
                    if answer.get('phase') == 'unavailable':
                        raise ScopeProtocolError(str(answer.get('message', 'Vérification du scope impossible.'))[:500])
                    if answer.get('phase') != 'result' or set(answer) != {'phase', 'report'} or not isinstance(answer.get('report'), dict):
                        raise ScopeProtocolError('Résultat du superviseur absent ou inattendu.')
                    candidate = answer['report']
                    if candidate.get('exercise') != '42/c/' + exercise.removeprefix('42/c/'):
                        raise ScopeProtocolError('Exercice du rapport incohérent.')
                    if candidate.get('result') not in ('passed', 'failed', 'incomplete') or not isinstance(candidate.get('checks'), list):
                        raise ScopeProtocolError('Rapport de correction invalide.')
                    checks = candidate['checks']
                    if len(checks) > 128 or any(not isinstance(c, dict) or c.get('status') not in ('pass', 'fail', 'unavailable', 'info') or not isinstance(c.get('name'), str) or not isinstance(c.get('message'), str) for c in checks):
                        raise ScopeProtocolError('Contrôles du rapport invalides.')
                    expected_result = ('failed' if any(c['status'] == 'fail' for c in checks) else
                                       'incomplete' if any(c['status'] == 'unavailable' for c in checks) else 'passed')
                    if candidate['result'] != expected_result:
                        raise ScopeProtocolError('Statut et contrôles du rapport incohérents.')
                    if expected_result == 'passed':
                        _validate_favorable_checks(exercise, checks)
                    limits = candidate.get('cgroup_limits')
                    if not isinstance(limits, dict) or limits != {'pids_max': state['pids_max'], 'memory_max': state['memory_max'], 'cpu_quota': state['cpu_quota'], 'cpu_period': state['cpu_period'], 'swap_max': 0}:
                        raise ScopeProtocolError('Limites du rapport incohérentes.')
                    report = candidate
                if proc.wait(timeout=10) != 0:
                    raise ScopeProtocolError('Le superviseur ne s’est pas terminé normalement.')
            except KeyboardInterrupt as exc:
                error = 'Correction interrompue ; arrêt du scope demandé.'
                if getattr(exc, '_moulinette_cleanup_error', None):
                    error += ' Nettoyage de processus non confirmé.'
            except (OSError, subprocess.TimeoutExpired, ScopeProtocolError, CgroupGateUnavailable, ValueError) as exc:
                error = f'Cgroup expérimental indisponible ou résultat ambigu : {exc}'
            finally:
                # Une unité transitoire appartient uniquement à cette évaluation.
                _stop(systemctl, scope, env)
                if proc is not None and proc.poll() is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except OSError:
                        pass
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        error = (error + ' ' if error else '') + 'Arrêt du lanceur non confirmé.'
                if base is not None and not _wait_unpopulated(base):
                    error = (error + ' ' if error else '') + 'Nettoyage du cgroup non confirmé ; résultat non validé.'
                elif base is None and proc is not None:
                    error = (error or 'Contrôle du scope interrompu.') + ' Nettoyage du cgroup non confirmé.'
    if error:
        return None, error
    if report is None:
        return None, 'Aucun rapport confirmé ; correction arrêtée.'
    return report, None

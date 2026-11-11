"""Témoin cgroup v2 limité : ne lance ni compilateur ni code étudiant.

Un scope utilisateur transitoire exécute un programme fixe. Huit enfants
au maximum sont créés ; un tube libère tous les enfants et un signal d'alarme
borne la durée. Aucun test d'épuisement mémoire ou du noyau n'est réalisé.
Le résultat reste incomplet : ce n'est pas une sandbox pour du code hostile.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

# Ce témoin est du code fixe, jamais fourni par un étudiant. Les limites sont
# pour la sonde seulement : elles ne sont pas des valeurs de production.
PROBE = r'''
import errno, json, os, signal
from pathlib import Path

signal.alarm(6)
children = []
read_end = write_end = None
result = {'status': 'unavailable'}
try:
    rows = Path('/proc/self/cgroup').read_text().splitlines()
    group = next((r[3:] for r in rows if r.startswith('0::')), None)
    if group is None or not group.startswith('/') or '..' in Path(group).parts:
        raise ValueError('chemin cgroup v2 indisponible ou inattendu')
    root = Path('/sys/fs/cgroup').resolve()
    base = (root / group.lstrip('/')).resolve()
    if not base.is_relative_to(root):
        raise ValueError('chemin cgroup hors de la hiérarchie visible')
    members = (base / 'cgroup.procs').read_text().split()
    if str(os.getpid()) not in members:
        raise ValueError('appartenance au cgroup non confirmée')
    pids_max = (base / 'pids.max').read_text().strip()
    memory_max = (base / 'memory.max').read_text().strip()
    cpu_max = (base / 'cpu.max').read_text().strip().split()
    initial = int((base / 'pids.current').read_text().strip())
    def max_events():
        pairs = [line.split() for line in (base / 'pids.events').read_text().splitlines()]
        return int(next(p[1] for p in pairs if len(p) == 2 and p[0] == 'max'))
    before_events = max_events()
    # Aucun enfant tant que les limites ne sont pas confirmées.
    if pids_max != '8' or memory_max != str(128 * 1024 * 1024):
        raise ValueError('limites de processus ou de mémoire inattendues')
    if len(cpu_max) != 2 or cpu_max[0] == 'max' or int(cpu_max[0]) != int(cpu_max[1]):
        raise ValueError('limite CPU inattendue ou indisponible')
    if not 1 <= initial < 8:
        raise ValueError('nombre initial de tâches incompatible avec le témoin')
    read_end, write_end = os.pipe()
    rejected = False
    current_at_rejection = None
    for _ in range(8):
        try:
            pid = os.fork()
        except OSError as exc:
            if exc.errno != errno.EAGAIN:
                raise
            rejected = True
            current_at_rejection = int((base / 'pids.current').read_text().strip())
            break
        if pid == 0:
            try:
                signal.alarm(6)
                os.close(write_end)
                os.read(read_end, 1)
            finally:
                os._exit(0)
        children.append(pid)
    after_events = max_events()
    result = {'status': 'observed' if rejected and len(children) > 0 and current_at_rejection == 8 and after_events > before_events else 'unavailable',
              'pids_max': pids_max, 'memory_max': memory_max, 'cpu_max': ' '.join(cpu_max),
              'initial_tasks': initial, 'children_created': len(children),
              'tasks_at_rejection': current_at_rejection, 'pids_events_delta': after_events - before_events,
              'rejected': rejected}
except Exception as exc:
    result = {'status': 'unavailable', 'error': type(exc).__name__ + ': ' + str(exc)[:300]}
finally:
    # EOF libère tous les enfants ; ils ne gardent pas l'extrémité écriture.
    if write_end is not None:
        os.close(write_end)
    if read_end is not None:
        os.close(read_end)
    reaped = 0
    for child in children:
        try:
            os.waitpid(child, 0)
            reaped += 1
        except ChildProcessError:
            pass
    result['children_reaped'] = reaped
    print(json.dumps(result, separators=(',', ':')), flush=True)
    signal.alarm(0)
'''


def cgroup_selftest():
    checks = []
    def add(name, status, message):
        checks.append({'name': name, 'status': status, 'message': message})
    def finish():
        return {'checks': checks, 'result': 'failed' if any(c['status'] == 'fail' for c in checks) else 'incomplete',
                'purpose': 'sonde limitée, pas de correction ni de validation de sécurité'}
    run = shutil.which('systemd-run')
    if not run or not Path('/usr/bin/python3').is_file():
        add('Prérequis', 'unavailable', 'systemd-run ou Python système absent.'); return finish()
    command = [run, '--user', '--scope', '--quiet', '-p', 'TasksMax=8',
               '-p', 'MemoryMax=128M', '-p', 'CPUQuota=100%', '--',
               '/usr/bin/python3', '-I', '-c', PROBE]
    env = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'LANG') if key in os.environ}
    env.update({'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    try:
        p = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        add('Scope de test', 'unavailable', f'Sonde non achevée : {exc}'); return finish()
    if p.returncode != 0:
        add('Scope de test', 'unavailable', (p.stderr.strip() or f'Code de sortie {p.returncode}.')[:800]); return finish()
    try:
        if len(p.stdout) > 8192 or p.stderr.strip():
            raise ValueError('sortie inattendue')
        data = json.loads(p.stdout)
        if not isinstance(data, dict) or data.get('status') not in ('observed', 'unavailable'):
            raise ValueError('format inconnu')
        if data['status'] == 'observed':
            if (data.get('pids_max') != '8' or data.get('memory_max') != str(128 * 1024 * 1024)
                or not isinstance(data.get('cpu_max'), str) or data.get('rejected') is not True
                or type(data.get('tasks_at_rejection')) is not int or data['tasks_at_rejection'] != 8
                or type(data.get('pids_events_delta')) is not int or data['pids_events_delta'] < 1
                or type(data.get('children_created')) is not int or not 1 <= data['children_created'] <= 7
                or type(data.get('children_reaped')) is not int or data['children_reaped'] != data['children_created']):
                raise ValueError('mesures incohérentes')
            cpu = data['cpu_max'].split()
            if (len(cpu) != 2 or not all(x.isdecimal() for x in cpu) or int(cpu[0]) <= 0
                or int(cpu[0]) != int(cpu[1]) or type(data.get('initial_tasks')) is not int
                or data['initial_tasks'] + data['children_created'] != 8):
                raise ValueError('limite CPU ou nombre initial incohérent')
    except (ValueError, TypeError):
        add('Scope de test', 'unavailable', 'Réponse de la sonde invalide ou incohérente.'); return finish()
    if data['status'] != 'observed':
        detail = str(data.get('error', 'Refus de création non attribuable avec certitude à la limite demandée.'))[:400]
        add('Limite de tâches', 'unavailable', detail); return finish()
    add('Scope et limites', 'pass', f"pids.max={data['pids_max']} ; memory.max={data['memory_max']} ; cpu.max={data['cpu_max']}.")
    add('Témoin de limite de tâches', 'pass', f"Refus observé à {data['tasks_at_rejection']} tâches ; compteur pids.events augmenté de {data['pids_events_delta']}.")
    add('Nettoyage du témoin', 'pass', f"{data['children_reaped']} enfant(s) attendu(s) et récupérés.")
    add('Limites non testées', 'unavailable', 'Mémoire en charge, CPU, stockage, intégration au correcteur et sécurité globale non validés.')
    return finish()

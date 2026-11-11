"""Sonde de faisabilité bubblewrap. N'exécute aucun code étudiant.

Ces quelques sondes ne constituent ni une sandbox de correction, ni une
certification de sécurité, ni un test des limites de ressources.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
from .seccomp_filter import seccomp_fd

PROBE = r'''import errno, json, os, socket, sys
path, port = sys.argv[1], int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.5)
try:
    s.connect(('127.0.0.1', port))
    connected = True
except OSError:
    connected = False
finally:
    s.close()
ns = {}
for name in ('user', 'mnt', 'pid', 'net'):
    try: ns[name] = os.readlink('/proc/self/ns/' + name)
    except OSError: ns[name] = None
seccomp_blocked = False
if hasattr(os, 'unshare'):
    try:
        os.unshare(0x10000000)
    except OSError as exc:
        seccomp_blocked = (exc.errno == errno.EPERM)
print(json.dumps({'canary_visible': os.path.exists(path),
                  'env_visible': 'MOULINETTE_DOCTOR_CANARY' in os.environ,
                  'host_loopback_reachable': connected, 'namespaces': ns,
                  'seccomp_blocked': seccomp_blocked}))
'''


def _host_namespaces():
    result = {}
    for name in ('user', 'mnt', 'pid', 'net'):
        try: result[name] = os.readlink('/proc/self/ns/' + name)
        except OSError: result[name] = None
    return result


def diagnose():
    checks = []
    def add(name, status, detail): checks.append({'name': name, 'status': status, 'message': detail})
    def finish():
        return {'checks': checks, 'result': 'failed' if any(x['status'] == 'fail' for x in checks) else 'incomplete', 'purpose': 'diagnostic de faisabilité uniquement ; isolation de correction non disponible'}
    bwrap = shutil.which('bwrap')
    if not bwrap:
        add('Bubblewrap', 'unavailable', 'bwrap introuvable. Sur Ubuntu : sudo apt install bubblewrap.')
        return finish()
    python = Path('/usr/bin/python3')
    if not python.exists():
        add('Python système', 'unavailable', '/usr/bin/python3 absent ; diagnostic indisponible.')
        return finish()
    try:
        version = subprocess.run([bwrap, '--version'], capture_output=True, text=True, timeout=5, check=False, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
        if version.returncode:
            add('Bubblewrap', 'unavailable', 'Impossible de lire la version de bwrap.')
            return finish()
        add('Bubblewrap', 'pass', version.stdout.strip() or 'Détecté.')
        with tempfile.TemporaryDirectory(prefix='moulinette-doctor-') as folder, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server, seccomp_fd() as sfd:
            canary = Path(folder) / 'canary.txt'
            canary.write_text('fichier témoin sans donnée sensible', encoding='utf-8')
            server.bind(('127.0.0.1', 0)); server.listen(1)
            port = server.getsockname()[1]
            host_ns = _host_namespaces()
            env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'MOULINETTE_DOCTOR_CANARY': secrets.token_hex(8)}
            args = [bwrap, *(['--seccomp', str(sfd)] if sfd is not None else []),
                    '--unshare-all', '--die-with-parent', '--new-session',
                    '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
                    '--symlink', 'usr/lib', '/lib',
                    *(['--symlink', 'usr/lib64', '/lib64'] if Path('/usr/lib64').exists() else []),
                    '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
                    '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin', '--',
                    '/usr/bin/python3', '-c', PROBE, str(canary), str(port)]
            p = subprocess.run(args, capture_output=True, text=True, timeout=10, env=env, check=False,
                               pass_fds=() if sfd is None else (sfd,))
            if p.returncode != 0:
                detail = p.stderr.strip()[:800] or f'bwrap est sorti avec le code {p.returncode}.'
                add('Lancement du diagnostic', 'unavailable', detail)
                return finish()
            try:
                data = json.loads(p.stdout)
                if not isinstance(data, dict) or any(not isinstance(data.get(k), bool) for k in ('canary_visible', 'env_visible', 'host_loopback_reachable')) or not isinstance(data.get('namespaces'), dict):
                    raise ValueError('format inattendu')
            except (ValueError, TypeError):
                add('Lancement du diagnostic', 'unavailable', 'Réponse de la sonde incorrecte ou illisible.')
                return finish()
            add('Fichier témoin', 'fail' if data['canary_visible'] else 'pass', 'Visible dans la sonde.' if data['canary_visible'] else 'Non visible dans la sonde.')
            add('Variable témoin', 'fail' if data['env_visible'] else 'pass', 'Visible dans la sonde.' if data['env_visible'] else 'Non visible dans la sonde.')
            add('Réseau local témoin', 'fail' if data['host_loopback_reachable'] else 'pass', 'Le port local témoin est accessible.' if data['host_loopback_reachable'] else 'Le port local témoin est inaccessible depuis la sonde.')
            for name in ('user', 'mnt', 'pid', 'net'):
                before, after = host_ns.get(name), data['namespaces'].get(name)
                if not before or not after:
                    add('Namespace ' + name, 'unavailable', 'Identification impossible.')
                else:
                    add('Namespace ' + name, 'pass' if before != after else 'fail', 'Différent du processus parent.' if before != after else 'Identique au processus parent.')
            if sfd is not None and data.get('seccomp_blocked') is True:
                add('Filtre seccomp (partiel)', 'pass', 'Appels administratifs bloqués (unshare refusé avec EPERM) dans la sonde x86_64.')
            elif sfd is not None:
                add('Filtre seccomp (partiel)', 'fail', 'Le filtre seccomp n’a pas bloqué l’appel témoin dans la sonde.')
    except (OSError, subprocess.TimeoutExpired) as exc:
        add('Diagnostic', 'unavailable', f'Impossible de terminer la sonde : {exc}')
    add('Limites et protection', 'unavailable', 'Filtre seccomp partiel uniquement (liste noire limitée sur x86_64) ; pas de limite de processus hors mode cgroup ni d’isolement complet du correcteur.')
    return finish()

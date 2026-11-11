"""Superviseur expérimental : ne corrige rien avant vérification et accord.

Pas une sandbox pour code non fiable. L'accès au canal est protégé uniquement
par les permissions du répertoire de l'utilisateur, pas contre le même UID.
"""
import argparse
import os
import socket
import sys
from pathlib import Path
from .cgroup_gate import CgroupGateUnavailable, verify_current_scope
from .cgroup_launcher import _termination_signals
from .scope_protocol import receive_object, send_object, ScopeProtocolError
from .checker import check_ex00, check_ex01, check_exercise
from .exercise_catalog import canonical_exercise


def serve(sock, scope):
    sock.settimeout(15)
    try:
        # Aucun accès au rendu ni lancement du compilateur avant ces étapes.
        state = verify_current_scope(scope, swap_max=0)
        send_object(sock, {'phase': 'ready', 'pid': os.getpid(), 'scope': scope})
        request = receive_object(sock)
        if (set(request) != {'action', 'path', 'exercise'} or request['action'] != 'run'
            or not isinstance(request['path'], str) or not request['path'] or len(request['path']) > 8192
            or canonical_exercise(request['exercise']) is None
            or request['path'].startswith(('https://', 'http://', 'git@'))):
            raise ScopeProtocolError('Demande de correction invalide.')
        state = verify_current_scope(scope, swap_max=0)
        exercise = canonical_exercise(request['exercise'])
        if exercise == 'c00/ex00':
            report = check_ex00(Path(request['path']), sandbox=True)
        elif exercise == 'c00/ex01':
            report = check_ex01(Path(request['path']), sandbox=True)
        else:
            report = check_exercise(Path(request['path']), exercise, sandbox=True)
        report['isolation'] = 'Bubblewrap et cgroup expérimentaux — code de confiance uniquement'
        for check in report.get('checks', []):
            if check.get('name') == 'Limites':
                check['message'] = ('Bubblewrap et cgroup expérimentaux : code de confiance seulement, '
                                    'pas de seccomp ni protection complète. Les limites et contrôles restent partiels.')
        report['cgroup_limits'] = {'pids_max': state['pids_max'], 'memory_max': state['memory_max'],
                                  'cpu_quota': state['cpu_quota'], 'cpu_period': state['cpu_period'], 'swap_max': 0}
        send_object(sock, {'phase': 'result', 'report': report})
        return 0
    except KeyboardInterrupt as exc:
        detail = getattr(exc, '_moulinette_cleanup_error', None)
        try:
            send_object(sock, {'phase':'unavailable', 'message':'Correction interrompue ; nettoyage demandé.' + (' ' + detail if detail else '')})
        except ScopeProtocolError:
            pass
        return 2
    except (CgroupGateUnavailable, ScopeProtocolError, OSError, ValueError) as exc:
        try:
            send_object(sock, {'phase': 'unavailable', 'message': str(exc)[:500]})
        except ScopeProtocolError:
            pass
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--socket', required=True)
    parser.add_argument('--scope', required=True)
    args = parser.parse_args(argv)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect(args.socket)
            with _termination_signals():
                return serve(sock, args.scope)
    except OSError as exc:
        print(f'Superviseur cgroup indisponible : {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())

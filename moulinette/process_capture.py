"""Capture bornée de processus de confiance, réservée à Linux.

Une sortie tronquée est signalée par une longueur atteignant le plafond.
Ce superviseur ne constitue pas une sandbox et n'empêche pas des descendants
qui changent de groupe ou se mettent en état noyau non interruptible.
"""
import os
import selectors
import signal
import subprocess
import sys
import time


def append_cleanup_error(exc, message):
    """Conserver tous les diagnostics sans masquer l'exception d'origine."""
    previous = getattr(exc, '_moulinette_cleanup_error', None)
    exc._moulinette_cleanup_error = (previous + ' ' if previous else '') + message
    if hasattr(exc, 'add_note'):
        exc.add_note(message)


def exception_with_cleanup(exc):
    detail = getattr(exc, '_moulinette_cleanup_error', None)
    return str(exc) + (' ' + detail if detail else '')


def run_bounded(cmd, cwd, timeout, env, setup_limits, *, pass_fds=(), max_stdout=131072, max_stderr=131072, stdin=None):
    # waitid(WNOWAIT) garde le chef zombie jusqu'au signalement du groupe :
    # son PID ne peut alors pas être recyclé avant killpg. Linux seulement.
    required = ('waitid', 'P_PID', 'WEXITED', 'WNOHANG', 'WNOWAIT')
    if not all(hasattr(os, name) for name in required):
        raise OSError('Supervision waitid indisponible ; aucune commande lancée.')
    proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL if stdin is None else stdin, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, preexec_fn=setup_limits, start_new_session=True,
                            env=env, pass_fds=pass_fds, bufsize=0)
    deadline = time.monotonic() + timeout
    outputs = {'out': bytearray(), 'err': bytearray()}
    limits = {'out': max_stdout, 'err': max_stderr}
    timed_out = False
    group_signalled = False
    identity_safe = True
    cleanup_error = None
    grace_deadline = None

    def stop_group():
        nonlocal group_signalled
        if group_signalled or not identity_safe:
            return
        # Le chef n'a pas été récolté : le PID reste réservé même s'il est mort.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            group_signalled = True

    try:
        with selectors.DefaultSelector() as selector:
            for stream, key in ((proc.stdout, 'out'), (proc.stderr, 'err')):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, key)
            while True:
                now = time.monotonic()
                if not group_signalled:
                    try:
                        finished = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    except ChildProcessError as exc:
                        identity_safe = False
                        raise OSError('État du processus perdu ; nettoyage non confirmé.') from exc
                    if finished is not None:
                        stop_group()
                        grace_deadline = now + 0.5
                    elif now >= deadline:
                        timed_out = True
                        stop_group()
                        grace_deadline = now + 0.5
                if group_signalled and not selector.get_map():
                    break
                if group_signalled and now >= grace_deadline:
                    raise OSError('Des sorties restent ouvertes après arrêt du groupe ; nettoyage non confirmé.')
                limit = grace_deadline if group_signalled else deadline
                delay = max(0.0, min(0.025, limit - now))
                if not selector.get_map():
                    time.sleep(delay)
                    continue
                for key, _ in selector.select(delay):
                    try:
                        chunk = os.read(key.fileobj.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    else:
                        target = outputs[key.data]
                        if len(target) < limits[key.data]:
                            target.extend(chunk[:limits[key.data] - len(target)])
    finally:
        original_exception = sys.exc_info()[1]
        try:
            stop_group()
        except OSError as exc:
            cleanup_error = f'Arrêt du groupe impossible : {exc}'
        for stream in (proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()
        try:
            proc.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            cleanup_error = (cleanup_error + ' ' if cleanup_error else '') + 'Arrêt du processus non confirmé après le délai de nettoyage.'
        if cleanup_error:
            if original_exception is None:
                raise OSError(cleanup_error)
            # Ne pas masquer l'interruption, mais conserver le diagnostic.
            append_cleanup_error(original_exception, cleanup_error)
    return proc.returncode, bytes(outputs['out']), bytes(outputs['err']), timed_out


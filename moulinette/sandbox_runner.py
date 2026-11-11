"""Prototype Bubblewrap ; ne convient toujours pas au code non fiable.

Pas de cgroup/seccomp, noyau partagé ; ressources et montage partiellement bornés.
Pas de fallback automatique vers l'hôte.
"""
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from .exercise_catalog import EXERCISES
from .process_capture import append_cleanup_error
from .seccomp_filter import seccomp_fd


class SandboxUnavailable(Exception):
    """Infrastructure indisponible ou résultat ambigu : ne pas poursuivre."""


class ExperimentalRunner:
    def __init__(self, run_command, exercise="c00/ex00"):
        self.bwrap = shutil.which('bwrap')
        if not self.bwrap:
            raise SandboxUnavailable('Bubblewrap introuvable ; aucune exécution locale de secours ne sera lancée.')
        self.run_command = run_command
        if exercise not in EXERCISES:
            raise SandboxUnavailable('Exercice inconnu : aucune opération de sandbox autorisée.')
        self.source = EXERCISES[exercise]['source']
        self.test_binary = EXERCISES[exercise]['executable']

    def __call__(self, cmd, cwd, timeout, limited=False):
        work = Path(cwd).resolve()
        target = Path(cmd[0]).resolve()
        norm_binary = shutil.which('norminette')
        is_norm = bool(norm_binary and target == Path(norm_binary).resolve())
        san_binary = self.test_binary + '-san'
        is_test = target in (work / self.test_binary, work / san_binary)
        active_binary = san_binary if target == work / san_binary else self.test_binary
        venv = None
        compile_mounts = None
        destination = None
        created_identity = None
        created_fd = None
        if is_norm:
            if tuple(map(str, cmd[1:])) not in (('--version',), ('-f', 'json', '--no-colors', self.source)) or limited:
                raise SandboxUnavailable('Commande Norminette non reconnue ; lancement refusé.')
            venv = target.parent.parent
            home = Path.home().resolve()
            protected = {Path('/'), Path('/tmp'), Path('/var'), Path('/usr'), Path('/usr/local'), Path('/opt'), home, home / '.local', home / '.local' / 'share'}
            cfg = venv / 'pyvenv.cfg'
            if (venv in protected or home.is_relative_to(venv) or cfg.is_symlink()
                or not cfg.is_file() or not (venv / 'bin/python').exists()):
                raise SandboxUnavailable('Norminette doit être installée dans un environnement virtuel dédié ; aucun dossier personnel large ne sera monté.')
            exe = '/opt/norminette/bin/python'
        elif is_test:
            exe = '/work/' + active_binary
        elif target in {Path(found).resolve() for name in ('cc', 'nm') if (found := shutil.which(name))}:
            if not target.is_file() or not target.is_relative_to('/usr'):
                raise SandboxUnavailable('Outil système hors de /usr ou introuvable ; lancement refusé.')
            exe = str(target)
            # Commandes internes strictement définies. /work est un tmpfs borné ;
            # seules les entrées nécessaires sont montées et un unique fichier
            # de sortie prédéfini est accessible en écriture sur l'hôte.
            cc = Path(shutil.which('cc')).resolve() if shutil.which('cc') else None
            nm = Path(shutil.which('nm')).resolve() if shutil.which('nm') else None
            operations = {
                (cc, ('-Wall', '-Wextra', '-Werror', '-fno-builtin', '-c', self.source, '-o', 'submission.o')): ((self.source,), 'submission.o'),
                (cc, ('-Wall', '-Wextra', '-Werror', '-fno-builtin', '-fno-stack-protector', '-c', self.source, '-o', 'submission-nocanary.o')): ((self.source,), 'submission-nocanary.o'),
                (cc, ('-Wall', '-Wextra', '-Werror', '-fno-builtin', '-Dmain=__moulinette_student_main', '-Wno-unused-function', '-Wno-return-type', '-c', self.source, '-o', 'submission-nomain.o')): ((self.source,), 'submission-nomain.o'),
                (cc, ('-Wall', '-Wextra', '-Werror', '-fno-builtin', '-Dmain=__moulinette_student_main', '-Wno-unused-function', '-Wno-return-type', '-fno-stack-protector', '-c', self.source, '-o', 'submission-nomain.o')): ((self.source,), 'submission-nomain.o'),
                (cc, ('-Wall', '-Wextra', '-Werror', '-fno-builtin', '-fsanitize=undefined', '-fsanitize-undefined-trap-on-error', '-c', self.source, '-o', 'submission-san.o')): ((self.source,), 'submission-san.o'),
                (cc, ('-Wall', '-Wextra', '-Werror', '-fno-builtin', '-Dmain=__moulinette_student_main', '-Wno-unused-function', '-Wno-return-type', '-fsanitize=undefined', '-fsanitize-undefined-trap-on-error', '-c', self.source, '-o', 'submission-san.o')): ((self.source,), 'submission-san.o'),
                (nm, ('-u', 'submission.o')): (('submission.o',), None),
                (nm, ('-u', 'submission-nocanary.o')): (('submission-nocanary.o',), None),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', '-c', 'proto_check.c', '-o', 'proto_check.o')): (('proto_check.c', self.source), 'proto_check.o'),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', 'submission.o', '-o', self.test_binary)): (('submission.o',), self.test_binary),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', 'submission-nocanary.o', '-o', self.test_binary)): (('submission-nocanary.o',), self.test_binary),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', 'submission-san.o', '-o', san_binary)): (('submission-san.o',), san_binary),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', 'harness.c', 'submission.o', '-o', self.test_binary)): (('harness.c', 'submission.o'), self.test_binary),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', 'harness.c', 'submission-nocanary.o', '-o', self.test_binary)): (('harness.c', 'submission-nocanary.o'), self.test_binary),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', 'harness.c', 'submission-nomain.o', '-o', self.test_binary)): (('harness.c', 'submission-nomain.o'), self.test_binary),
                (cc, ('-Wall', '-Wextra', '-Werror', '-std=c11', '-fsanitize=undefined', '-fsanitize-undefined-trap-on-error', 'harness.c', 'submission-san.o', '-o', san_binary)): (('harness.c', 'submission-san.o'), san_binary),
            }
            compile_mounts = operations.get((target, tuple(map(str, cmd[1:]))))
            if compile_mounts is None:
                raise SandboxUnavailable('Commande de compilation ou analyse non reconnue ; lancement refusé.')
        else:
            raise SandboxUnavailable(f'Outil non autorisé par le prototype : {target.name}.')
        if not is_norm and is_test != bool(limited):
            raise SandboxUnavailable('Étape ou mode de montage incohérent ; lancement refusé.')
        keep_output = False
        try:
            with tempfile.TemporaryFile() as status_file, seccomp_fd() as sfd:
                command = [self.bwrap, '--json-status-fd', str(status_file.fileno()),
                           *(['--seccomp', str(sfd)] if sfd is not None else []),
                           '--unshare-all', '--die-with-parent', '--new-session',
                           '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
                           '--symlink', 'usr/lib', '/lib']
                if Path('/usr/lib64').exists():
                    command += ['--symlink', 'usr/lib64', '/lib64']
                if not is_test:
                    command += ['--proc', '/proc']
                command += ['--dev', '/dev', '--size', str(1024*1024 if is_test else 32*1024*1024), '--tmpfs', '/tmp']
                if is_norm:
                    command += ['--dir', '/work', '--ro-bind', str(work / self.source), '/work/' + self.source, '--ro-bind', str(venv), '/opt/norminette']
                elif is_test:
                    command += ['--dir', '/work', '--ro-bind', str(work / active_binary), '/work/' + active_binary]
                else:
                    inputs, output = compile_mounts
                    command += ['--size', str(32 * 1024 * 1024), '--tmpfs', '/work']
                    for name in inputs:
                        source = work / name
                        if not source.is_file() or source.is_symlink():
                            raise SandboxUnavailable(f'Fichier d’entrée absent ou inattendu : {name}.')
                        command += ['--ro-bind', str(source), '/work/' + name]
                    if output:
                        destination = work / output
                        try:
                            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
                        except OSError as exc:
                            raise SandboxUnavailable(f'Création exclusive du fichier de sortie impossible : {output}.') from exc
                        created_fd = fd
                        created = os.fstat(fd)
                        created_identity = (created.st_dev, created.st_ino)
                        command += ['--bind', str(destination), '/work/' + output]
                command += ['--chdir', '/work', '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
                            '--setenv', 'LC_ALL', 'C', '--', exe]
                if is_norm:
                    command += ['-I', '-B', '-m', 'norminette']
                command += list(map(str, cmd[1:]))
                fds = (status_file.fileno(),) if sfd is None else (status_file.fileno(), sfd)
                result = self.run_command(command, cwd, timeout, limited=limited, pass_fds=fds)
                code, _, _, timed_out = result
                status_file.seek(0)
                raw = status_file.read(8193)
            if timed_out:
                step = 'test fonctionnel' if is_test else 'Norminette' if is_norm else 'compilation ou analyse'
                raise SandboxUnavailable(f'Délai dépassé pendant {step} ; démarrage ou exécution non confirmé, correction arrêtée.')
            try:
                if len(raw) > 8192:
                    raise ValueError('rapport trop long')
                events = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
                if len(events) != 2 or not isinstance(events[0], dict) or type(events[0].get('child-pid')) is not int or events[0]['child-pid'] <= 0 or not isinstance(events[1], dict) or type(events[1].get('exit-code')) is not int or events[1]['exit-code'] != code:
                    raise ValueError('rapport incomplet ou incohérent')
            except (UnicodeError, ValueError, TypeError):
                raise SandboxUnavailable('Bubblewrap n’a pas fourni de statut complet et cohérent ; correction arrêtée.')
            if destination is not None and code == 0:
                try:
                    output_info = destination.lstat()
                    if ((output_info.st_dev, output_info.st_ino) != created_identity or not stat.S_ISREG(output_info.st_mode) or output_info.st_nlink != 1 or not 0 < output_info.st_size <= 16 * 1024 * 1024):
                        raise ValueError('sortie absente, vide, inhabituelle ou trop volumineuse')
                except (OSError, ValueError):
                    raise SandboxUnavailable('La sortie de compilation est absente ou incohérente ; correction arrêtée.')
            keep_output = (code == 0)
            return result
        finally:
            try:
                if destination is not None and created_identity is not None and not keep_output:
                    original_exception = sys.exc_info()[1]
                    try:
                        try: info=destination.lstat()
                        except FileNotFoundError: info=None
                        if info is not None:
                            if ((info.st_dev,info.st_ino) != created_identity or
                                not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
                                raise OSError('identité de la sortie modifiée')
                            # Contrôle indicatif uniquement : une course même UID
                            # peut encore se produire entre lstat et unlink.
                            destination.unlink()
                    except OSError as exc:
                        message=f'Nettoyage de la sortie de compilation non confirmé : {exc}'
                        if original_exception is None:
                            raise SandboxUnavailable(message) from exc
                        append_cleanup_error(original_exception, message)
            finally:
                if created_fd is not None: os.close(created_fd)

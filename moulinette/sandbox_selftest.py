"""Test contrôlé de compilation et exécution Bubblewrap, non une sandbox générale.

Seuls des programmes témoins constants définis ici sont compilés et exécutés.
Ne donne aucune garantie pour du code étudiant non fiable.
"""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile

SOURCE = r'''#include <arpa/inet.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    int fd, writer, sock, connected;
    struct sockaddr_in addr = {0};
    if (argc != 3) return 10;
    fd = open(argv[1], O_RDONLY);
    if (fd >= 0) close(fd);
    writer = open("/work/write-check", O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (writer >= 0) close(writer);
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return 11;
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)atoi(argv[2]));
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    connected = connect(sock, (struct sockaddr *)&addr, sizeof(addr)) == 0;
    close(sock);
    printf("%d %d %d %d\n", fd < 0, writer < 0,
           getenv("MOULINETTE_SELFTEST_CANARY") == NULL, !connected);
    return 0;
}
'''


def _command(bwrap, work, readonly, command):
    return [bwrap, '--unshare-all', '--die-with-parent', '--new-session',
            '--ro-bind', '/usr', '/usr', '--symlink', 'usr/bin', '/bin',
            '--symlink', 'usr/lib', '/lib',
            *(['--symlink', 'usr/lib64', '/lib64'] if Path('/usr/lib64').exists() else []),
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
            '--ro-bind' if readonly else '--bind', str(work), '/work',
            '--chdir', '/work', '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
            '--setenv', 'LC_ALL', 'C', '--', *command]


def _run(command):
    # These are trusted, fixed programs, not a runner for user-supplied code.
    env = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'MOULINETTE_SELFTEST_CANARY': 'present-on-parent-only'}
    return subprocess.run(command, capture_output=True, text=True, timeout=15, check=False, env=env)


def selftest():
    checks = []
    def add(name, status, message): checks.append({'name': name, 'status': status, 'message': message})
    def finish():
        result = 'failed' if any(c['status'] == 'fail' for c in checks) else 'incomplete'
        return {'checks': checks, 'result': result, 'purpose': 'preuve de faisabilité avec témoins de confiance, correcteur toujours non isolé'}
    bwrap = shutil.which('bwrap')
    if not bwrap:
        add('Bubblewrap', 'unavailable', 'bwrap introuvable ; installer bubblewrap si souhaité.'); return finish()
    cc = Path('/usr/bin/cc').resolve()
    if not cc.is_file() or not cc.is_relative_to('/usr'):
        add('Compilateur', 'unavailable', 'Compilateur système introuvable ou situé hors de /usr.'); return finish()
    try:
        with tempfile.TemporaryDirectory(prefix='moulinette-selftest-') as tmp:
            root = Path(tmp); work = root / 'work'; work.mkdir()
            secret = root / 'canary.txt'; secret.write_text('MOULINETTE_TEST_SECRET_FAKE', encoding='ascii')
            (work / 'probe.c').write_text(SOURCE, encoding='utf-8')
            build = _run(_command(bwrap, work, False, [str(cc), '-Wall', '-Wextra', '-Werror', 'probe.c', '-o', 'probe']))
            if build.returncode or not (work / 'probe').is_file():
                add('Compilation témoin', 'unavailable', (build.stderr.strip() or f'Code de sortie {build.returncode}.')[:1000]); return finish()
            add('Compilation témoin', 'pass', 'Programme témoin compilé dans Bubblewrap.')
            (work / 'probe-include.c').write_text('#include ' + json.dumps(str(secret)) + '\nint main(void) { return 0; }\n', encoding='utf-8')
            include = _run(_command(bwrap, work, False, [str(cc), '-c', 'probe-include.c', '-o', 'probe-include.o']))
            # Requérir une erreur connue de fichier manquant ; un échec indéterminé n'est pas une preuve.
            if include.returncode != 0 and 'No such file or directory' in include.stderr and 'MOULINETTE_TEST_SECRET_FAKE' not in include.stderr:
                add('Fichier témoin à la compilation', 'pass', 'Le préprocesseur ne trouve pas le fichier témoin externe.')
            else:
                add('Fichier témoin à la compilation', 'fail', 'Protection non confirmée ou sortie du compilateur inattendue.')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.bind(('127.0.0.1', 0)); server.listen(1)
                run = _run(_command(bwrap, work, True, ['/work/probe', str(secret), str(server.getsockname()[1])]))
            if run.returncode != 0 or not re.fullmatch(r'[01] [01] [01] [01]\n', run.stdout):
                add('Exécution témoin', 'unavailable', (run.stderr.strip() or 'Sortie de la sonde inattendue.')[:1000]); return finish()
            add('Exécution témoin', 'pass', 'Binaire témoin exécuté dans une nouvelle instance Bubblewrap.')
            fields = run.stdout.strip().split()
            for label, val, success in zip(('Fichier témoin à l’exécution', 'Répertoire de travail en lecture seule', 'Variable témoin', 'Port local témoin'), fields,
                    ('Fichier externe inaccessible.', 'Écriture refusée.', 'Variable absente.', 'Port local inaccessible.')):
                ok = val == '1'
                if label == 'Répertoire de travail en lecture seule' and (work / 'write-check').exists(): ok = False
                add(label, 'pass' if ok else 'fail', success if ok else 'La vérification n’a pas confirmé la restriction.')
    except (OSError, subprocess.TimeoutExpired) as exc:
        add('Test expérimental', 'unavailable', f'Test non achevé : {exc}')
    add('Limites non testées', 'unavailable', 'Limitation des processus, seccomp, cgroups et exécution sécurisée du correcteur non implémentés ni validés.')
    return finish()

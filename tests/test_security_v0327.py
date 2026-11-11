"""Régressions légères : uniquement fichiers temporaires et petites sorties."""
import ast
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from moulinette import cli, live, cpp_engine, github_bounded
from moulinette.checker import MAX_FILE


class SecurityRegression(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='moulinette-security-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_fichier_isole_copie_bornee_et_refusee(self):
        src = self.root / 'ft_ft.c'
        src.write_bytes(b'x' * (MAX_FILE + 4096))
        with cli.stage_submission_path(src, 'c01/ex00') as staged:
            copied = staged / src.name
            self.assertEqual(copied.stat().st_size, MAX_FILE + 1)
            report = cli.check_exercise(staged, 'c01/ex00', sandbox=False)
            self.assertNotEqual(report['result'], 'passed')

    def test_lien_remplace_entre_inventaire_et_ouverture(self):
        src = self.root / 'ft_ft.c'
        victim = self.root / 'victime'
        src.write_text('intact'); victim.write_text('secret')
        original = os.open
        def swap(path, flags, *args, **kwargs):
            if Path(path) == src:
                src.unlink(); src.symlink_to(victim)
            return original(path, flags, *args, **kwargs)
        with patch('moulinette.cli.os.open', side_effect=swap):
            with self.assertRaises(OSError):
                with cli.stage_submission_path(src, 'c01/ex00'):
                    self.fail('un lien final ne doit pas être suivi')

    def test_fichier_etat_remplace_lien_sans_modifier_cible(self):
        data = self.root / 'data'; data.mkdir()
        app = data / 'moulinette-lab'; app.mkdir()
        victim = self.root / 'victim'; victim.write_text('intact')
        state = app / 'live-daemon.json'; state.symlink_to(victim)
        class Server:
            server_address = ('127.0.0.1', 12345)
            daemon_threads = False
            def serve_forever(self): pass
            def server_close(self): pass
        with patch.dict(os.environ, {'XDG_DATA_HOME': str(data)}), \
             patch('moulinette.live.ThreadingHTTPServer', return_value=Server()), \
             patch('moulinette.live.write_dashboard'):
            live.serve(open_browser=False, announce=lambda x: None)
        self.assertEqual(victim.read_text(), 'intact')
        self.assertFalse(state.is_symlink())
        self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o600)

    def test_live_termine_si_preparation_echoue(self):
        run = live.Run('test')
        with patch('moulinette.cli.stage_submission_path', side_effect=OSError('erreur simulée')):
            live.execute_run(run, self.root, 'c01/ex00', True, True)
        self.assertTrue(run.finished)
        self.assertEqual(run.events[-1]['type'], 'done')
        self.assertEqual(run.events[-1]['result'], 'incomplete')

    def test_stdin_cpp_et_capture_limitee(self):
        # 10 Kio de sortie : contrôle de troncature, pas de charge active.
        code = "import sys; d=sys.stdin.buffer.read(); sys.stdout.buffer.write(d+b'x'*10000)"
        with patch('moulinette.cpp_engine.MAX_CAPTURE', 512):
            status, out, err, timed = cpp_engine._run_cmd([sys.executable, '-c', code], self.root, 5, stdin_bytes=b'bonjour')
        self.assertEqual(status, 0)
        self.assertEqual(len(out), 512)
        self.assertTrue(out.startswith(b'bonjour'))
        self.assertFalse(timed)
        self.assertEqual(err, b'')

    def test_modules_worker_git_importables_en_isolation(self):
        tree = ast.parse(Path(github_bounded.__file__).read_text())
        fn = next(x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef) and x.name == '_fetch_snapshot')
        assign = next(x for x in ast.walk(fn) if isinstance(x, ast.Assign) and any(isinstance(z, ast.Name) and z.id == 'modules' for z in x.targets))
        modules = ast.literal_eval(assign.value)
        dest = self.root / 'isolated' / 'moulinette'; dest.mkdir(parents=True)
        source = Path(github_bounded.__file__).parent
        for name in modules:
            shutil.copyfile(source / name, dest / name)
        result = subprocess.run([sys.executable, '-I', '-B', '-c',
                                 'import sys;sys.path.insert(0,sys.argv[1]);import moulinette.github_worker', str(dest.parent)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == '__main__': unittest.main()

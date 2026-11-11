import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette.checker import check_ex00
from moulinette.sandbox_doctor import diagnose

COMPILE_ARGS = ['-Wall', '-Wextra', '-Werror', '-fno-builtin', '-c', 'ft_putchar.c', '-o', 'submission.o']

GOOD = '#include <unistd.h>\nvoid ft_putchar(char c) { write(1, &c, 1); }\n'

class ExperimentalFailClosedTests(unittest.TestCase):
    def test_missing_bwrap_no_host_fallback(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_putchar.c').write_text(GOOD)
            with patch('moulinette.sandbox_runner.shutil.which', return_value=None), \
                 patch('moulinette.checker._run', side_effect=AssertionError('exécution locale interdite')):
                report = check_ex00(path, sandbox=True)
        self.assertEqual(report['result'], 'incomplete')
        self.assertTrue(any(x['name'] == 'Bubblewrap expérimental' and x['status'] == 'unavailable' for x in report['checks']))

    @unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
    def test_failed_bwrap_does_not_fallback(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_putchar.c').write_text(GOOD)
            with patch('moulinette.checker._run', return_value=(1, b'', b'bwrap: setup failed', False)) as run:
                report = check_ex00(path, sandbox=True)
        self.assertEqual(report['result'], 'incomplete')
        self.assertEqual(run.call_count, 1)
        self.assertTrue(any('Bubblewrap' in c['name'] and c['status'] == 'unavailable' for c in report['checks']))

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap, cc et nm requis')
class ExperimentalIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        report = diagnose()
        relevant = [x for x in report['checks'] if x['name'] not in ('Limites et protection',)]
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            raise unittest.SkipTest('Bubblewrap ne fonctionne pas dans cet environnement')

    def test_trusted_example_through_bwrap(self):
        path = Path(__file__).resolve().parent.parent / 'exemples' / 'ft_putchar'
        with patch("moulinette.checker.check_norm", return_value=("unavailable", "norm absente dans ce test")):
            report = check_ex00(path, sandbox=True)
        self.assertEqual(report['result'], 'incomplete')
        self.assertTrue(any(x['name'] == 'Test 256 octets successifs' and x['status'] == 'pass' for x in report['checks']))
        self.assertTrue(any(x['name'] == 'Norminette adaptée' and x['status'] == 'unavailable' for x in report['checks']))

    def test_preprocessor_cannot_read_known_canary(self):
        with tempfile.TemporaryDirectory(prefix='moulinette-canary-') as tmp:
            root = Path(tmp); rend = root / 'rend'; rend.mkdir()
            canary = root / 'secret.h'; canary.write_text('VISIBLE_CANARY_CONTENT\n')
            (rend / 'ft_putchar.c').write_text(f'#include "{canary}"\nvoid ft_putchar(char c) {{ (void)c; }}\n')
            report = check_ex00(rend, sandbox=True)
        compilation = next(x for x in report['checks'] if x['name'] == 'Compilation')
        self.assertEqual(compilation['status'], 'fail')
        self.assertNotIn('VISIBLE_CANARY_CONTENT', compilation['message'])
        self.assertIn('No such file or directory', compilation['message'])

class BubblewrapStatusTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
    def test_child_stderr_cannot_impersonate_bwrap_setup_failure(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            os.write(pass_fds[0], b'{"child-pid":123}\n{"exit-code":1}\n')
            return 1, b'', b'bwrap: message de l enfant', False
        with tempfile.TemporaryDirectory() as t:
            runner = ExperimentalRunner(fake)
            (Path(t) / 'ft_putchar.c').write_text(GOOD)
            result = runner([shutil.which('cc'), *COMPILE_ARGS], Path(t), 2)
        self.assertEqual(result[0], 1)
        self.assertTrue(result[2].startswith(b'bwrap:'))

    @unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
    def test_incomplete_or_missing_status_never_proceeds(self):
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            return 0, b'', b'', False
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'ft_putchar.c').write_text(GOOD)
            with self.assertRaises(SandboxUnavailable):
                ExperimentalRunner(fake)([shutil.which('cc'), *COMPILE_ARGS], Path(t), 2)

    @unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
    def test_timeout_never_proceeds(self):
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            return -9, b'', b'', True
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'ft_putchar.c').write_text(GOOD)
            with self.assertRaises(SandboxUnavailable):
                ExperimentalRunner(fake)([shutil.which('cc'), *COMPILE_ARGS], Path(t), 2)

    @unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
    def test_test_execution_mounts_only_binary_and_bounded_tmp(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            self.assertIn('--size', command)
            self.assertEqual(command[command.index('--size') + 1], str(1024 * 1024))
            self.assertIn('/work/test-ex00', command)
            self.assertNotIn('--proc', command)
            self.assertNotIn(str(cwd), command[command.index('--dir'):])
            os.write(pass_fds[0], b'{"child-pid":123}\n{"exit-code":73}\n')
            return 73, b'A', b'', False
        with tempfile.TemporaryDirectory() as t:
            p = Path(t); (p/'test-ex00').write_text('fichier témoin')
            self.assertEqual(ExperimentalRunner(fake)([str(p/'test-ex00'), '65'], p, 2, limited=True)[0], 73)

class SourceSnapshotTests(unittest.TestCase):
    def test_hard_link_is_refused(self):
        import os
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); rend = root / 'rend'; rend.mkdir()
            original = root / 'original.c'; original.write_text(GOOD)
            os.link(original, rend / 'ft_putchar.c')
            report = check_ex00(rend)
        self.assertEqual(report['result'], 'failed')
        self.assertTrue(any('lien physique' in c['message'] for c in report['checks']))

def run_isolation_witness(code):
    """Witness explicitly exercises runner mounts, not the symbol-policy checker."""
    from moulinette.sandbox_runner import ExperimentalRunner
    from moulinette.checker import _run
    cc=shutil.which('cc')
    with tempfile.TemporaryDirectory() as t:
        work=Path(t)
        (work/'ft_putchar.c').write_text(code)
        (work/'harness.c').write_text('void ft_putchar(char); int main(void) { ft_putchar(65); return 0; }\n')
        runner=ExperimentalRunner(_run)
        comp=runner([cc,'-Wall','-Wextra','-Werror','-fno-builtin','-c','ft_putchar.c','-o','submission.o'],work,10)
        if comp[0] != 0: raise AssertionError(comp)
        link=runner([cc,'-Wall','-Wextra','-Werror','-std=c11','harness.c','submission.o','-o','test-ex00'],work,10)
        if link[0] != 0: raise AssertionError(link)
        return runner([str(work/'test-ex00'),'1'],work,3,limited=True)

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap, cc et nm requis')
class IsolatedWorkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        report = diagnose()
        relevant = [x for x in report['checks'] if x['name'] != 'Limites et protection']
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            raise unittest.SkipTest('Bubblewrap indisponible dans cet environnement')

    def test_harness_is_not_visible_to_student_process(self):
        code = '#include <fcntl.h>\n#include <unistd.h>\nvoid ft_putchar(char c) { int fd = open("/work/harness.c", O_RDONLY); if (fd < 0) write(1, &c, 1); else close(fd); }\n'
        status, out, err, timeout = run_isolation_witness(code)
        self.assertEqual((status, out, timeout), (0, b'A', False), err)

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm') and shutil.which('norminette'), 'bwrap, outils C et norminette requis')
class NormVenvIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        norm = Path(shutil.which('norminette')).resolve()
        version = subprocess.run([str(norm), '--version'], capture_output=True, text=True, timeout=10)
        if 'norminette 3.3.59' not in (version.stdout + version.stderr).lower() or not (norm.parent.parent / 'pyvenv.cfg').is_file():
            raise unittest.SkipTest('Norminette 3.3.59 dans un venv dédiée requise')
        relevant = [x for x in diagnose()['checks'] if x['name'] != 'Limites et protection']
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            raise unittest.SkipTest('Bubblewrap indisponible')

    def test_norm_ignores_header_only_in_sandbox(self):
        path = Path(__file__).resolve().parent.parent / 'exemples' / 'ft_putchar'
        report = check_ex00(path, sandbox=True)
        check = next(x for x in report['checks'] if x['name'] == 'Norminette adaptée')
        self.assertEqual(check['status'], 'pass')
        self.assertIn('INVALID_HEADER ignoré : 1', check['message'])

    def test_norm_still_reports_style_errors_in_sandbox(self):
        bad = '#include <unistd.h>\n\nvoid ft_putchar(char c)\n{\n    write(1, &c, 1);\n}\n'
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path / 'ft_putchar.c').write_text(bad)
            report = check_ex00(path, sandbox=True)
        check = next(x for x in report['checks'] if x['name'] == 'Norminette adaptée')
        self.assertEqual(check['status'], 'fail')
        self.assertIn('SPACE_BEFORE_FUNC', check['message'])


class AnchoredSourceTests(unittest.TestCase):
    def test_replaced_directory_does_not_redirect_source_open(self):
        import os
        old_open = os.open
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            rend = root / 'rend'; rend.mkdir()
            (rend / 'ft_putchar.c').write_text(GOOD)
            copied = []
            def racing_open(path, flags, *args, **kwargs):
                if path == 'ft_putchar.c' and kwargs.get('dir_fd') is not None:
                    rend.rename(root / 'old-rend')
                    rend.mkdir()
                    (rend / 'ft_putchar.c').write_text('REPLACEMENT')
                return old_open(path, flags, *args, **kwargs)
            def capture_compile(cmd, cwd, timeout, limited=False, pass_fds=()):
                copied.append((cwd / 'ft_putchar.c').read_text())
                return (1, b'', b'test de compilation interrompu', False)
            with patch('moulinette.checker.os.open', side_effect=racing_open), \
                 patch('moulinette.checker._run', side_effect=capture_compile):
                check_ex00(rend)
        self.assertEqual(copied, [GOOD])

    def test_final_directory_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); real = root / 'real'; real.mkdir()
            (real / 'ft_putchar.c').write_text(GOOD)
            link = root / 'link'; link.symlink_to(real, target_is_directory=True)
            report = check_ex00(link)
        self.assertEqual(report['result'], 'failed')
        self.assertTrue(any(x['name'] == 'Dossier' and x['status'] == 'fail' for x in report['checks']))


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap, cc et nm requis')
class CompilationMountTests(unittest.TestCase):
    def test_compilation_mounts_only_source_and_output(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner
        calls = []
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            calls.append(command)
            os.write(pass_fds[0], b'{"child-pid":123}\n{"exit-code":1}\n')
            return (1, b'', b'fake compiler error', False)
        with tempfile.TemporaryDirectory() as t:
            work = Path(t)
            (work/'ft_putchar.c').write_text(GOOD)
            (work/'harness.c').write_text('SECRET_HARNESS')
            runner = ExperimentalRunner(fake)
            runner([shutil.which('cc'), *COMPILE_ARGS], work, 10)
            cmd = calls[0]
            self.assertNotIn(str(work), cmd)
            self.assertIn(str(work / 'ft_putchar.c'), cmd)
            self.assertIn(str(work / 'submission.o'), cmd)
            self.assertNotIn(str(work / 'harness.c'), cmd)
            i = cmd.index('/work')
            self.assertEqual(cmd[i-1], '--tmpfs')
            self.assertEqual(cmd[i-3:i-1], ['--size', str(32 * 1024 * 1024)])
            self.assertEqual(cmd[cmd.index(str(work/'ft_putchar.c'))-1], '--ro-bind')
            self.assertEqual(cmd[cmd.index(str(work/'submission.o'))-1], '--bind')

    def test_unknown_command_and_preexisting_output_fail_closed(self):
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        with tempfile.TemporaryDirectory() as t:
            work = Path(t)
            (work/'ft_putchar.c').write_text(GOOD)
            (work/'submission.o').write_text('NE PAS MODIFIER')
            runner = ExperimentalRunner(lambda *a, **kw: self.fail('le programme ne doit pas démarrer'))
            with self.assertRaises(SandboxUnavailable):
                runner([shutil.which('cc'), '-c', 'x.c'], work, 10)
            with self.assertRaises(SandboxUnavailable):
                runner([shutil.which('cc'), *COMPILE_ARGS], work, 10)
            self.assertEqual((work/'submission.o').read_text(), 'NE PAS MODIFIER')

    def test_success_without_nonempty_output_fails_closed(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            os.write(pass_fds[0], b'{"child-pid":123}\n{"exit-code":0}\n')
            return (0, b'', b'', False)
        with tempfile.TemporaryDirectory() as t:
            work = Path(t); (work/'ft_putchar.c').write_text(GOOD)
            with self.assertRaises(SandboxUnavailable):
                ExperimentalRunner(fake)([shutil.which('cc'), *COMPILE_ARGS], work, 10)

    def test_tmpfs_rejects_writes_over_size_limit(self):
        from moulinette.checker import _run
        relevant = [x for x in diagnose()['checks'] if x['name'] != 'Limites et protection']
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            self.skipTest('Bubblewrap indisponible')
        code = (
            'import errno\n'
            'try:\n'
            ' f=open("/work/fill", "wb", buffering=0)\n'
            ' for i in range(4096): f.write(b"X"*4096)\n'
            'except OSError as e:\n'
            ' print("LIMIT" if e.errno == errno.ENOSPC else "OTHER")\n'
            'else: print("NOT_LIMITED")\n'
        )
        cmd = [shutil.which('bwrap'), '--unshare-all', '--die-with-parent',
               '--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib',
               '--symlink', 'usr/lib64', '/lib64', '--size', str(1024*1024), '--tmpfs', '/work',
               '--', '/usr/bin/python3', '-c', code]
        with tempfile.TemporaryDirectory() as t:
            status, out, err, timeout = _run(cmd, t, 10)
        self.assertFalse(timeout)
        self.assertEqual(status, 0, err.decode(errors='replace'))
        self.assertEqual(out.strip(), b'LIMIT')


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
class ProcessCleanupWitnessTests(unittest.TestCase):
    def test_timed_out_container_does_not_leave_test_child_running(self):
        import time
        from moulinette.checker import _run
        relevant = [x for x in diagnose()['checks'] if x['name'] != 'Limites et protection']
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            self.skipTest('Bubblewrap indisponible')
        # Témoin auto-terminant : aucun fork-bomb ni écriture hors du fichier temporaire.
        script = ('import os,time\n'
                  'if os.fork()==0:\n'
                  ' os.setsid(); time.sleep(1); open("/marker", "w").write("survived")\n'
                  'else: time.sleep(5)\n')
        with tempfile.TemporaryDirectory() as t:
            marker = Path(t) / 'marker'; marker.write_text('')
            cmd = [shutil.which('bwrap'), '--unshare-all', '--die-with-parent', '--new-session',
                   '--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib',
                   '--symlink', 'usr/lib64', '/lib64', '--bind', str(marker), '/marker',
                   '--', '/usr/bin/python3', '-c', script]
            _, _, err, timed_out = _run(cmd, t, 0.3)
            self.assertTrue(timed_out, err.decode(errors='replace'))
            time.sleep(1.2)
            self.assertEqual(marker.read_text(), '')


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'bwrap et cc requis')
class MoreStatusValidationTests(unittest.TestCase):
    def test_malformed_and_inconsistent_status_cannot_pass(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        for raw in (b'{bad json}\n', b'{"child-pid":true}\n{"exit-code":1}\n',
                    b'{"child-pid":0}\n{"exit-code":1}\n',
                    b'{"child-pid":123}\n{"exit-code":0}\n'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as t:
                work = Path(t); (work/'ft_putchar.c').write_text(GOOD)
                def fake(command, cwd, timeout, limited=False, pass_fds=()):
                    os.write(pass_fds[0], raw)
                    return (1, b'', b'', False)
                with self.assertRaises(SandboxUnavailable):
                    ExperimentalRunner(fake)([shutil.which('cc'), *COMPILE_ARGS], work, 2)


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap, cc et nm requis')
class AuditFixTests(unittest.TestCase):
    def test_output_inode_replacement_fails_closed(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            (cwd / 'submission.o').rename(cwd / 'old')
            (cwd / 'submission.o').write_text('remplacement non vide')
            os.write(pass_fds[0], b'{"child-pid":123}\n{"exit-code":0}\n')
            return (0, b'', b'', False)
        with tempfile.TemporaryDirectory() as t:
            work = Path(t); (work/'ft_putchar.c').write_text(GOOD)
            with self.assertRaises(SandboxUnavailable):
                ExperimentalRunner(fake)([shutil.which('cc'), *COMPILE_ARGS], work, 10)

    def test_unknown_norminette_command_is_rejected(self):
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        real_which = shutil.which
        with tempfile.TemporaryDirectory() as t:
            work = Path(t); venv = work / 'venv'; (venv / 'bin').mkdir(parents=True)
            norm = venv/'bin'/'norminette'; norm.write_text('')
            (venv/'bin'/'python').write_text('')
            (venv/'pyvenv.cfg').write_text('')
            def which(name):
                return str(norm) if name == 'norminette' else real_which(name)
            with patch('moulinette.sandbox_runner.shutil.which', side_effect=which):
                runner = ExperimentalRunner(lambda *a, **kw: self.fail('aucun lancement'))
                with self.assertRaises(SandboxUnavailable):
                    runner([str(norm), '--unexpected'], work, 10)

    def test_real_student_timeout_is_incomplete_and_identifies_phase(self):
        relevant = [x for x in diagnose()['checks'] if x['name'] != 'Limites et protection']
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            self.skipTest('Bubblewrap indisponible')
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_putchar.c').write_text('void ft_putchar(char c) { (void)c; while (1) {} }\n')
            report = check_ex00(path, sandbox=True)
        self.assertEqual(report['result'], 'incomplete')
        self.assertTrue(any(x['status'] == 'unavailable' and 'Délai dépassé pendant test fonctionnel' in x['message'] for x in report['checks']))


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap, cc et nm requis')
class AuditIntegrationRegressionTests(unittest.TestCase):
    def test_test_process_has_no_proc_mount(self):
        relevant = [x for x in diagnose()['checks'] if x['name'] != 'Limites et protection']
        if not relevant or any(x['status'] != 'pass' for x in relevant):
            self.skipTest('Bubblewrap indisponible')
        code = '#include <unistd.h>\nvoid ft_putchar(char c) { if (access("/proc/self/stat", F_OK) != 0) write(1, &c, 1); }\n'
        status, out, err, timeout = run_isolation_witness(code)
        self.assertEqual((status, out, timeout), (0, b'A', False), err)

    def test_child_pid_alone_does_not_classify_timeout_as_student_failure(self):
        import os
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        def fake(command, cwd, timeout, limited=False, pass_fds=()):
            os.write(pass_fds[0], b'{"child-pid":123}\n')
            return (-9, b'', b'', True)
        with tempfile.TemporaryDirectory() as t:
            work = Path(t); (work/'ft_putchar.c').write_text(GOOD)
            with self.assertRaises(SandboxUnavailable):
                ExperimentalRunner(fake)([shutil.which('cc'), *COMPILE_ARGS], work, 10)

class SymlinkSourceRegressionTests(unittest.TestCase):
    def test_only_source_symlink_is_rejected_without_compilation(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); rend = root/'rend'; rend.mkdir()
            source = root/'outside.c'; source.write_text(GOOD)
            (rend/'ft_putchar.c').symlink_to(source)
            with patch('moulinette.checker._run', side_effect=AssertionError('aucune exécution')):
                report = check_ex00(rend)
        self.assertEqual(report['result'], 'failed')
        self.assertTrue(any(c['name'] == 'Fichier attendu' and 'symbolique' in c['message'] for c in report['checks']))


if __name__ == '__main__':
    unittest.main()

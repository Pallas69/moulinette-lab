import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from moulinette.checker import check_ex00
from moulinette.norm import parse_norm_result
from unittest.mock import patch

GOOD = '#include <unistd.h>\nvoid ft_putchar(char c) { write(1, &c, 1); }\n'

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class CheckEx00Tests(unittest.TestCase):
    def evaluate(self, code, extra=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'ft_putchar.c').write_text(code)
            if extra:
                (path / extra).write_text('extra')
            return check_ex00(path)

    def test_correct_code_remains_incomplete_without_norm(self):
        with patch("moulinette.checker.check_norm", return_value=("unavailable", "test : Norminette absente")):
            r = self.evaluate(GOOD)
        self.assertEqual(r['result'], 'incomplete')
        self.assertEqual(sum(c['status'] == 'pass' and c['name'].startswith('Test ') for c in r['checks']), 10)
        self.assertTrue(any(c['name'] == 'Norminette adaptée' and c['status'] == 'unavailable' for c in r['checks']))

    def test_wrong_output(self):
        r = self.evaluate('#include <unistd.h>\nvoid ft_putchar(char c) { (void)c; write(1, "X", 1); }\n')
        self.assertEqual(r['result'], 'failed')
        self.assertTrue(any(x['name'] == 'Test lettre A' and x['status'] == 'fail' for x in r['checks']))

    def test_forbidden_symbol(self):
        r = self.evaluate('#include <stdio.h>\nvoid ft_putchar(char c) { putchar(c); }\n')
        self.assertTrue(any(x['name'] == 'Fonctions externes' and x['status'] == 'fail' and 'putchar' in x['message'] for x in r['checks']))

    def test_bad_prototype(self):
        r = self.evaluate('void ft_putchar(int c) { (void)c; }\n')
        self.assertTrue(any(x['name'] == 'Prototype' and x['status'] == 'fail' for x in r['checks']))

    def test_extra_file(self):
        r = self.evaluate(GOOD, 'surplus.txt')
        self.assertTrue(any(x['name'] == 'Fichiers supplémentaires' and x['status'] == 'fail' for x in r['checks']))

    def test_infinite_loop(self):
        r = self.evaluate('void ft_putchar(char c) { (void)c; while (1) {} }\n')
        self.assertTrue(any(x['status'] == 'fail' and 'Délai dépassé' in x['message'] for x in r['checks']))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path/'target').write_text(GOOD)
            (path/'ft_putchar.c').symlink_to(path/'target')
            self.assertEqual(check_ex00(path)['result'], 'failed')

    def test_successive_calls_detect_stateful_code(self):
        r = self.evaluate('#include <unistd.h>\nvoid ft_putchar(char c) { static int once; if (!once++) write(1, &c, 1); }\n')
        self.assertTrue(any(x['name'] == 'Test 256 octets successifs' and x['status'] == 'fail' for x in r['checks']))

    def test_local_function_cannot_link(self):
        r = self.evaluate('static void ft_putchar(char c) { (void)c; }\nvoid unused_test(void) { ft_putchar(0); }\n')
        self.assertTrue(any(x['name'] == 'Édition des liens' and x['status'] == 'fail' for x in r['checks']))

    def test_macro_type_redefinition_is_detected(self):
        r = self.evaluate('#define char int\nvoid ft_putchar(char c) { (void)c; }\n')
        self.assertTrue(any(x['name'] == 'Prototype' and x['status'] == 'fail' for x in r['checks']))

    def test_stderr_is_visible_but_not_assumed_forbidden_by_subject(self):
        r = self.evaluate('#include <unistd.h>\nvoid ft_putchar(char c) { write(1, &c, 1); write(2, "!", 1); }\n')
        self.assertTrue(any(x['name'] == 'Sortie stderr' and x['status'] == 'info' for x in r['checks']))

    def test_stack_protector_symbol_not_falsely_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cc = shutil.which('cc')
            wrapper = Path(tmp) / 'cc'
            wrapper.write_text('#!/bin/sh\nexec "' + cc + '" -fstack-protector-all "$@"\n')
            wrapper.chmod(0o755)
            import os
            with patch.dict(os.environ, {'PATH': tmp + ':' + os.environ['PATH']}):
                r = self.evaluate(GOOD)
        result = next(x for x in r['checks'] if x['name'] == 'Fonctions externes')
        self.assertEqual(result['status'], 'info')
        self.assertNotIn('__stack_chk_fail', result['message'])
        self.assertIn('-fno-stack-protector', next(x['message'] for x in r['checks'] if x['name'] == 'Adaptation compilation'))


class NormParserTests(unittest.TestCase):
    @staticmethod
    def data(errors, status='Error'):
        return ('Setting locale to en_US\n' + json.dumps({'files':[{'path':'ft_putchar.c','status':status,'errors':errors}]}, separators=(',', ':'))).encode()

    def test_filters_only_header(self):
        header = {'name':'INVALID_HEADER','text':'header','level':'Error','highlights':[{'lineno':1,'column':1}]}
        self.assertEqual(parse_norm_result(self.data([header]), 1)[0], 'pass')
        error = {'name':'SPACE_BEFORE_FUNC','text':'spacing','level':'Error','highlights':[{'lineno':1,'column':4}]}
        result = parse_norm_result(self.data([header,error]), 1)
        self.assertEqual(result[0], 'fail')
        self.assertIn('ligne 1 col 4', result[1])

    def test_malformed_json_is_incomplete(self):
        self.assertEqual(parse_norm_result(b'Setting locale to en_US\nnot json', 1)[0], 'unavailable')

    def test_unknown_extra_output_is_incomplete(self):
        self.assertEqual(parse_norm_result(b'unexpected\n' + self.data([], 'OK'), 0)[0], 'unavailable')

    def test_unknown_level_is_incomplete(self):
        item = {'name':'NEW_KIND','text':'?','level':'Warning','highlights':[]}
        self.assertEqual(parse_norm_result(self.data([item]), 1)[0], 'unavailable')

    def test_no_valid_json_error_never_passes(self):
        self.assertEqual(parse_norm_result(b'Error: Parse Error', 1)[0], 'unavailable')

class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'moulinette', *args], capture_output=True, text=True)

    def test_refuses_unisolated_by_default(self):
        # v0.31 : sans option, Bubblewrap est choisi s'il existe ; sinon refus.
        # Le mode local non isolé n'est jamais activé implicitement.
        import os
        env = dict(os.environ, PATH='/nonexistent')
        r = subprocess.run([sys.executable, '-m', 'moulinette', 'check', '.', '--exercise', 'c00/ex00'],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2)
        self.assertIn('pas sécurisé', r.stderr)
        self.assertIn('-l', r.stderr)

    def test_github_not_supported(self):
        r = self.run_cli('check', 'https://github.com/example/repo.git', '--exercise', 'c00/ex00', '--unsafe-local')
        self.assertEqual(r.returncode, 2)
        self.assertIn('GitHub', r.stderr)

    def test_dashboard_is_generated_without_opening_browser(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            env=dict(os.environ, XDG_DATA_HOME=tmp)
            r=subprocess.run([sys.executable, '-m', 'moulinette', 'dashboard', '--no-open'], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(tmp)/'moulinette-lab'/'dashboard.html').is_file())

class OutputExactnessRegressionTests(unittest.TestCase):
    """Cas établis après étude comparative de tests communautaires."""
    @unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
    def test_nul_absent_ne_doit_pas_passer(self):
        code = '#include <unistd.h>\nvoid ft_putchar(char c) { if (c != 0) write(1, &c, 1); }\n'
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_putchar.c').write_text(code)
            with patch('moulinette.checker.check_norm', return_value=('unavailable', 'hors sujet pour ce test')):
                report = check_ex00(path)
        self.assertTrue(any(c['name'] == 'Test NUL' and c['status'] == 'fail' for c in report['checks']))

    @unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
    def test_un_octet_supplementaire_doit_echouer(self):
        code = '#include <unistd.h>\nvoid ft_putchar(char c) { write(1, &c, 1); write(1, "!", 1); }\n'
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_putchar.c').write_text(code)
            with patch('moulinette.checker.check_norm', return_value=('unavailable', 'hors sujet pour ce test')):
                report = check_ex00(path)
        self.assertTrue(any(c['name'] == 'Test lettre A' and c['status'] == 'fail' for c in report['checks']))


class AuditFunctionalTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
    def test_exit_73_before_harness_returns_is_detected(self):
        code = '#include <unistd.h>\nvoid ft_putchar(char c) { write(1, &c, 1); _exit(73); }\n'
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path / 'ft_putchar.c').write_text(code)
            # Simuler une analyse acceptée uniquement pour exercer le témoin
            # de fin ; en production, l'appel _exit est désormais rejeté avant.
            from moulinette import checker
            actual_run = checker._run
            def witness_run(cmd, *args, **kwargs):
                if len(cmd) > 1 and cmd[1] == '-u': return (0, b' U write\n', b'', False)
                return actual_run(cmd, *args, **kwargs)
            with patch('moulinette.checker._run', side_effect=witness_run), patch('moulinette.checker.check_norm', return_value=('unavailable', 'test')):
                report = check_ex00(path)
        test = next(x for x in report['checks'] if x['name'] == 'Test lettre A')
        self.assertEqual(test['status'], 'fail')
        self.assertIn('Marqueur de fin du harnais absent', test['message'])

    def test_extra_files_stop_before_compilation(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_putchar.c').write_text(GOOD); (path/'surplus').write_text('x')
            with patch('moulinette.checker._run', side_effect=AssertionError('ne doit pas lancer le compilateur')):
                report = check_ex00(path)
        self.assertEqual(report['result'], 'failed')
        self.assertFalse(any(c['name'] == 'Compilation' for c in report['checks']))

    def test_change_during_source_read_is_marked_unavailable(self):
        import os
        from types import SimpleNamespace
        real_fstat = os.fstat
        seen = []
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); source = path/'ft_putchar.c'; source.write_text(GOOD)
            def fstat(fd):
                result = real_fstat(fd)
                try: target = os.readlink('/proc/self/fd/' + str(fd))
                except OSError: return result
                if target == str(source):
                    seen.append(1)
                    if len(seen) == 2:
                        return SimpleNamespace(st_size=result.st_size, st_mtime_ns=result.st_mtime_ns+1, st_ctime_ns=result.st_ctime_ns)
                return result
            with patch('moulinette.checker.os.fstat', side_effect=fstat), \
                 patch('moulinette.checker._run', side_effect=AssertionError('ne doit pas compiler')):
                report = check_ex00(path)
        self.assertEqual(len(seen), 2)
        self.assertEqual(report['result'], 'incomplete')
        self.assertTrue(any(c['name'] == 'Lecture du fichier' and c['status'] == 'unavailable' for c in report['checks']))


if __name__ == '__main__':
    unittest.main()

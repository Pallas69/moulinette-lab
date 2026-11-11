from support_audit import successful_report
import contextlib
import io
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette.checker import check_ex01
from moulinette import cli, cgroup_worker
from moulinette.scope_protocol import receive_object, send_object
import socket

GOOD = '#include <unistd.h>\nvoid ft_print_alphabet(void) { write(1, "abcdefghijklmnopqrstuvwxyz", 26); }\n'

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class AlphabetTests(unittest.TestCase):
    def evaluate(self, source, extra=None):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_print_alphabet.c').write_text(source)
            if extra: (path/extra).write_text('surplus')
            with patch('moulinette.checker.check_norm', return_value=('pass', 'test : style fictif')):
                return check_ex01(path)

    def test_valid_output_and_repeat_call(self):
        report = self.evaluate(GOOD)
        self.assertEqual(report['exercise'], '42/c/c00/ex01')
        self.assertEqual(report['result'], 'passed')
        self.assertEqual(sum(x['status'] == 'pass' and x['name'].startswith('Test ') for x in report['checks']), 2)
        self.assertTrue(any(x['name'] == 'Convention de test' and 'saut de ligne' in x['message'] for x in report['checks']))

    def test_wrong_case_order_or_length_fails(self):
        for text in ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'bacdefghijklmnopqrstuvwxyz', 'abcdefghijklmnopqrstuvwxy', 'abcdefghijklmnopqrstuvwxyz\n'):
            with self.subTest(text=text):
                escaped = text.replace('\n', '\\n')
                code = '#include <unistd.h>\nvoid ft_print_alphabet(void) { write(1, "' + escaped + '", ' + str(len(text)) + '); }\n'
                report = self.evaluate(code)
                check = next(x for x in report['checks'] if x['name'] == 'Test alphabet')
                self.assertEqual(check['status'], 'fail')
                self.assertIn('octet(s)', check['message'])

    def test_stateful_implementation_fails_second_call(self):
        code = '#include <unistd.h>\nvoid ft_print_alphabet(void) { static int once; if (!once++) write(1, "abcdefghijklmnopqrstuvwxyz", 26); }\n'
        report = self.evaluate(code)
        self.assertTrue(any(x['name'] == 'Test alphabet' and x['status'] == 'pass' for x in report['checks']))
        self.assertTrue(any(x['name'] == 'Test deux appels consécutifs' and x['status'] == 'fail' for x in report['checks']))

    def test_wrong_prototype_fails(self):
        report = self.evaluate('void ft_print_alphabet(int x) { (void)x; }\n')
        self.assertTrue(any(x['name'] == 'Prototype' and x['status'] == 'fail' for x in report['checks']))

    def test_forbidden_function_is_reported(self):
        report = self.evaluate('#include <stdio.h>\nvoid ft_print_alphabet(void) { puts("abcdefghijklmnopqrstuvwxyz"); }\n')
        self.assertTrue(any(x['name'] == 'Fonctions externes' and x['status'] == 'fail' and 'puts' in x['message'] for x in report['checks']))

    def test_extra_file_stops_before_compilation(self):
        report = self.evaluate(GOOD, 'surplus.c')
        self.assertEqual(report['result'], 'failed')
        self.assertFalse(any(x['name'] == 'Compilation' for x in report['checks']))

    def test_norminette_receives_correct_filename(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_print_alphabet.c').write_text(GOOD)
            with patch('moulinette.checker.check_norm', return_value=('pass', 'test')) as norm:
                check_ex01(path)
        self.assertEqual(norm.call_args.args[2], 'ft_print_alphabet.c')

class AlphabetDispatchTests(unittest.TestCase):
    def test_cli_dispatches_ex01(self):
        report = {'result':'passed', 'checks':[]}
        with patch('moulinette.cli.check_ex01', return_value=report) as ex01, \
             patch('moulinette.cli.check_ex00', side_effect=AssertionError('mauvais exercice')), \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(['check', '.', '--exercise', 'c00/ex01', '--unsafe-local','--no-history'])
        self.assertEqual(code, 0); self.assertEqual(ex01.call_count, 1)

    def test_worker_dispatches_ex01_after_gate(self):
        parent, child = socket.socketpair(); results=[]
        state={'scope':'scope', 'pids_max':32, 'memory_max':536870912, 'cpu_quota':100000, 'cpu_period':100000}
        report={'result':'passed', 'checks':[], 'exercise':'42/c/c00/ex01'}
        def worker():
            with child: results.append(cgroup_worker.serve(child, 'scope'))
        with parent, patch('moulinette.cgroup_worker.verify_current_scope', return_value=state), \
             patch('moulinette.cgroup_worker.check_ex01', return_value=report) as ex01, \
             patch('moulinette.cgroup_worker.check_ex00', side_effect=AssertionError('mauvais exercice')):
            parent.settimeout(2); thread=threading.Thread(target=worker); thread.start()
            self.assertEqual(receive_object(parent)['phase'], 'ready')
            send_object(parent, {'action':'run', 'path':'/test', 'exercise':'c00/ex01'})
            data=receive_object(parent); thread.join(2)
        self.assertEqual(data['report']['exercise'], '42/c/c00/ex01')
        self.assertEqual(results,[0]); self.assertEqual(ex01.call_count, 1)


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm') and shutil.which('norminette'), 'bwrap, cc, nm et norminette requis')
class AlphabetSandboxIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        from moulinette.sandbox_doctor import diagnose
        norm = Path(shutil.which('norminette')).resolve()
        version = subprocess.run([str(norm), '--version'], capture_output=True, text=True, timeout=10)
        if 'norminette 3.3.59' not in (version.stdout + version.stderr).lower() or not (norm.parent.parent / 'pyvenv.cfg').is_file():
            raise unittest.SkipTest('Norminette 3.3.59 en venv requis')
        checks = [x for x in diagnose()['checks'] if x['name'] != 'Limites et protection']
        if not checks or any(x['status'] != 'pass' for x in checks):
            raise unittest.SkipTest('Bubblewrap indisponible')

    def test_valid_example_with_real_bwrap_and_norminette(self):
        path = Path(__file__).resolve().parent.parent / 'exemples' / 'ft_print_alphabet'
        report = check_ex01(path, sandbox=True)
        self.assertEqual(report['result'], 'passed')
        self.assertTrue(any(x['name'] == 'Test deux appels consécutifs' and x['status'] == 'pass' for x in report['checks']))
        self.assertTrue(any(x['name'] == 'Norminette adaptée' and x['status'] == 'pass' for x in report['checks']))

    def test_style_failure_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t); (path/'ft_print_alphabet.c').write_text(GOOD)
            report = check_ex01(path, sandbox=True)
        check = next(x for x in report['checks'] if x['name'] == 'Norminette adaptée')
        self.assertEqual(check['status'], 'fail')

class AlphabetCgroupErrorTests(unittest.TestCase):
    def test_unavailable_scope_reports_the_requested_exercise(self):
        import json
        with patch('moulinette.cli.launch_cgroup', return_value=(None, 'scope indisponible')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code=cli.main(['check', '.', '--exercise', 'c00/ex01', '--experimental-cgroup-sandbox', '--json','--no-history'])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue())['exercise'], '42/c/c00/ex01')


class AlphabetCgroupFlowTests(unittest.TestCase):
    def test_simulated_scope_launcher_round_trip_for_ex01(self):
        from moulinette import cgroup_launcher
        import subprocess
        base = {'pids_max':32, 'memory_max':536870912, 'cpu_quota':100000, 'cpu_period':100000}
        report=successful_report('c00/ex01')
        class FakeProcess:
            def __init__(self, cmd, **kwargs):
                scope = next(x.split('=',1)[1] for x in cmd if x.startswith('--unit='))
                sockpath = cmd[cmd.index('--socket')+1]
                state=dict(base,scope=scope,group='/user.slice/'+scope)
                self.code=None; self.pid=999999
                def worker():
                    with patch('moulinette.cgroup_worker.verify_current_scope', return_value=state), \
                         patch('moulinette.cgroup_worker.check_ex01', return_value=dict(report)), \
                         patch('moulinette.cgroup_worker.check_ex00', side_effect=AssertionError('mauvais exercice')):
                        self.code=cgroup_worker.main(['--socket',sockpath,'--scope',scope])
                self.thread=threading.Thread(target=worker); self.thread.start()
            def poll(self): return self.code
            def wait(self, timeout=None):
                self.thread.join(timeout)
                if self.thread.is_alive(): raise subprocess.TimeoutExpired('fake',timeout)
                return self.code
        def gate(scope, **kwargs): return dict(base,scope=scope,group='/user.slice/'+scope)
        with patch('moulinette.cgroup_launcher.shutil.which', side_effect=lambda n:'/usr/bin/'+n), \
             patch('moulinette.cgroup_launcher.subprocess.Popen', FakeProcess), \
             patch('moulinette.cgroup_launcher.verify_current_scope', side_effect=gate), \
             patch('moulinette.cgroup_launcher._events', side_effect=[1,0]), \
             patch('moulinette.cgroup_launcher._stop'):
            actual,error=cgroup_launcher.launch('/trusted','c00/ex01')
        self.assertIsNone(error)
        self.assertEqual(actual['exercise'],'42/c/c00/ex01')
        self.assertEqual(actual['result'],'passed')

if __name__ == '__main__':
    unittest.main()

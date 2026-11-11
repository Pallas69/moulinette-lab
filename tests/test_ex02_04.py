from support_audit import successful_report
import contextlib
import io
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import canonical_exercise
from moulinette import cli, cgroup_worker
from moulinette.scope_protocol import receive_object, send_object
import socket

REVERSE = '#include <unistd.h>\nvoid ft_print_reverse_alphabet(void) { write(1, "zyxwvutsrqponmlkjihgfedcba", 26); }\n'
NUMBERS = '#include <unistd.h>\nvoid ft_print_numbers(void) { write(1, "0123456789", 10); }\n'
SIGN = '#include <unistd.h>\nvoid ft_is_negative(int n) { if (n < 0) write(1, "N", 1); else write(1, "P", 1); }\n'

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class C00BatchTests(unittest.TestCase):
    def evaluate(self, exercise, filename, code):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t); (path/filename).write_text(code)
            with patch('moulinette.checker.check_norm', return_value=('pass','style simulé')):
                return check_exercise(path, exercise)

    def test_valid_ex02_ex03_ex04(self):
        for exercise,name,code in [('c00/ex02','ft_print_reverse_alphabet.c',REVERSE),
                                   ('c00/ex03','ft_print_numbers.c',NUMBERS),
                                   ('c00/ex04','ft_is_negative.c',SIGN)]:
            with self.subTest(exercise=exercise):
                report=self.evaluate(exercise,name,code)
                self.assertEqual(report['exercise'],'42/c/'+exercise)
                self.assertEqual(report['result'],'passed')

    def test_wrong_order_and_characters_fail(self):
        wrong_reverse=REVERSE.replace('zyxwvutsrqponmlkjihgfedcba','abcdefghijklmnopqrstuvwxyz')
        wrong_numbers=NUMBERS.replace('0123456789','1234567890')
        for exercise,name,code in [('c00/ex02','ft_print_reverse_alphabet.c',wrong_reverse),
                                   ('c00/ex03','ft_print_numbers.c',wrong_numbers)]:
            with self.subTest(exercise=exercise):
                self.assertEqual(self.evaluate(exercise,name,code)['result'],'failed')

    def test_stateful_output_fails_repeat_call(self):
        code='#include <unistd.h>\nvoid ft_print_numbers(void) { static int done; if (!done++) write(1, "0123456789", 10); }\n'
        report=self.evaluate('c00/ex03','ft_print_numbers.c',code)
        self.assertTrue(any(x['name']=='Test deux appels consécutifs' and x['status']=='fail' for x in report['checks']))

    def test_zero_is_positive_and_extremes_work(self):
        wrong=SIGN.replace('n < 0', 'n <= 0')
        report=self.evaluate('c00/ex04','ft_is_negative.c',wrong)
        self.assertTrue(any(x['name']=='Test zéro' and x['status']=='fail' for x in report['checks']))
        good=self.evaluate('c00/ex04','ft_is_negative.c',SIGN)
        for name in ('Test int minimum','Test int maximum','Test deux signes consécutifs'):
            self.assertTrue(any(x['name']==name and x['status']=='pass' for x in good['checks']))

    def test_extra_output_and_incorrect_prototype_are_rejected(self):
        extra=SIGN.replace('write(1, "N", 1)', 'write(1, "N!", 2)')
        report=self.evaluate('c00/ex04','ft_is_negative.c',extra)
        self.assertTrue(any(x['name']=='Test négatif -1' and x['status']=='fail' for x in report['checks']))
        report=self.evaluate('c00/ex04','ft_is_negative.c','void ft_is_negative(unsigned int n) { (void)n; }\n')
        self.assertTrue(any(x['name']=='Prototype' and x['status']=='fail' for x in report['checks']))

    def test_norm_filename_is_specific(self):
        for exercise,filename,code in [('c00/ex02','ft_print_reverse_alphabet.c',REVERSE),
                                       ('c00/ex03','ft_print_numbers.c',NUMBERS),
                                       ('c00/ex04','ft_is_negative.c',SIGN)]:
            with self.subTest(exercise=exercise), tempfile.TemporaryDirectory() as t:
                p=Path(t); (p/filename).write_text(code)
                with patch('moulinette.checker.check_norm',return_value=('pass','test')) as norm:
                    check_exercise(p,exercise)
                self.assertEqual(norm.call_args.args[2],filename)

class DispatchTests(unittest.TestCase):
    def test_known_ids_and_unknown_are_strict(self):
        self.assertEqual(canonical_exercise('42/c/c00/ex04'),'c00/ex04')
        for value in ('c00/ex09','c00/ex04/../ex00','ex04',None,{}):
            self.assertIsNone(canonical_exercise(value))

    def test_cli_dispatch_and_unavailable_scope_identity(self):
        report={'result':'passed','checks':[]}
        with patch('moulinette.cli.check_exercise', return_value=report) as checker, \
             contextlib.redirect_stdout(io.StringIO()):
            code=cli.main(['check','.','--exercise','c00/ex04','--unsafe-local','--no-history'])
        self.assertEqual(code,0)
        self.assertEqual(checker.call_args.args[1],'c00/ex04')
        import json
        with patch('moulinette.cli.launch_cgroup',return_value=(None,'scope indisponible')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code=cli.main(['check','.','--exercise','c00/ex04','--experimental-cgroup-sandbox','--json','--no-history'])
        self.assertEqual(code,2)
        self.assertEqual(json.loads(out.getvalue())['exercise'],'42/c/c00/ex04')

    def test_worker_dispatches_ex04_after_scope_validation(self):
        parent, child=socket.socketpair(); results=[]
        state={'scope':'scope','pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
        report={'result':'passed','checks':[],'exercise':'42/c/c00/ex04'}
        def worker():
            with child: results.append(cgroup_worker.serve(child,'scope'))
        with parent, patch('moulinette.cgroup_worker.verify_current_scope',return_value=state), \
             patch('moulinette.cgroup_worker.check_exercise',return_value=report) as checker, \
             patch('moulinette.cgroup_worker.check_ex00',side_effect=AssertionError('mauvais exercice')):
            parent.settimeout(2); thread=threading.Thread(target=worker); thread.start()
            self.assertEqual(receive_object(parent)['phase'],'ready')
            send_object(parent,{'action':'run','path':'/trusted','exercise':'c00/ex04'})
            self.assertEqual(receive_object(parent)['report']['exercise'],'42/c/c00/ex04'); thread.join(2)
        self.assertEqual(results,[0]); self.assertEqual(checker.call_args.args[1],'c00/ex04')

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm') and shutil.which('norminette'), 'bwrap, cc, nm et norminette requis')
class RealSandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        from moulinette.sandbox_doctor import diagnose
        norm=Path(shutil.which('norminette')).resolve()
        version=subprocess.run([str(norm),'--version'],capture_output=True,text=True,timeout=10)
        if 'norminette 3.3.59' not in (version.stdout+version.stderr).lower() or not (norm.parent.parent/'pyvenv.cfg').is_file():
            raise unittest.SkipTest('Norminette 3.3.59 en venv requise')
        checks=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not checks or any(x['status']!='pass' for x in checks): raise unittest.SkipTest('Bubblewrap indisponible')

    def test_all_new_examples_in_real_bwrap_and_norminette(self):
        root=Path(__file__).resolve().parent.parent/'exemples'
        for exercise,folder in [('c00/ex02','ft_print_reverse_alphabet'),('c00/ex03','ft_print_numbers'),('c00/ex04','ft_is_negative')]:
            with self.subTest(exercise=exercise):
                report=check_exercise(root/folder,exercise,sandbox=True)
                self.assertEqual(report['result'],'passed',report)
                self.assertTrue(any(x['name']=='Norminette adaptée' and x['status']=='pass' for x in report['checks']))


class CgroupScopeBatchFlowTests(unittest.TestCase):
    def test_simulated_ex04_launcher_to_worker_and_back(self):
        import subprocess
        from moulinette import cgroup_launcher
        base={'pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
        report=successful_report('c00/ex04')
        class FakeProcess:
            def __init__(self,cmd,**kwargs):
                scope=next(x.split('=',1)[1] for x in cmd if x.startswith('--unit='))
                sockpath=cmd[cmd.index('--socket')+1]; self.code=None; self.pid=999999
                state=dict(base,scope=scope,group='/user.slice/'+scope)
                def worker():
                    with patch('moulinette.cgroup_worker.verify_current_scope',return_value=state), \
                         patch('moulinette.cgroup_worker.check_exercise',return_value=dict(report)):
                        self.code=cgroup_worker.main(['--socket',sockpath,'--scope',scope])
                self.thread=threading.Thread(target=worker); self.thread.start()
            def poll(self): return self.code
            def wait(self,timeout=None):
                self.thread.join(timeout)
                if self.thread.is_alive(): raise subprocess.TimeoutExpired('fake',timeout)
                return self.code
        def gate(scope,**kwargs): return dict(base,scope=scope,group='/user.slice/'+scope)
        with patch('moulinette.cgroup_launcher.shutil.which',side_effect=lambda n:'/usr/bin/'+n), \
             patch('moulinette.cgroup_launcher.subprocess.Popen',FakeProcess), \
             patch('moulinette.cgroup_launcher.verify_current_scope',side_effect=gate), \
             patch('moulinette.cgroup_launcher._events',side_effect=[1,0]), \
             patch('moulinette.cgroup_launcher._stop'):
            actual,error=cgroup_launcher.launch('/trusted','c00/ex04')
        self.assertIsNone(error)
        self.assertEqual(actual['exercise'],'42/c/c00/ex04')
        self.assertEqual(actual['result'],'passed')

if __name__ == '__main__':
    unittest.main()

from support_audit import successful_report
import contextlib
import io
import math
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES, INT_MIN_PY, INT_MAX_PY, _digit_combinations, _two_number_combinations
from moulinette import cli, cgroup_worker
from moulinette.scope_protocol import receive_object, send_object
import socket

ROOT = Path(__file__).resolve().parent.parent / 'exemples'

class OracleTests(unittest.TestCase):
    def test_ex05_all_distinct_ascending_triples(self):
        raw = _digit_combinations(3).decode('ascii')
        values = raw.split(', ')
        self.assertEqual(len(values), 120)
        self.assertEqual((values[0],values[-1]),('012','789'))
        self.assertEqual(values, sorted(set(values)))
        self.assertTrue(all(len(x)==3 and x[0]<x[1]<x[2] for x in values))
        self.assertFalse(raw.endswith(', '))

    def test_ex06_all_4950_ordered_pairs(self):
        raw = _two_number_combinations().decode('ascii'); values = raw.split(', ')
        self.assertEqual(len(values),4950)
        self.assertEqual((values[0],values[-1]),('00 01','98 99'))
        self.assertEqual(values,sorted(set(values)))
        self.assertTrue(all(len(x)==5 and x[2]==' ' and int(x[:2])<int(x[3:]) for x in values))
        self.assertFalse(raw.endswith(', '))
        self.assertGreater(len(raw)*2,65536)  # Régression sur la troncature des deux appels.

    def test_ex08_all_in_scope_n_and_boundaries(self):
        for n in range(1,10):
            with self.subTest(n=n):
                raw=_digit_combinations(n).decode('ascii'); values=raw.split(', ')
                self.assertEqual(len(values), math.comb(10,n))
                self.assertEqual(values[0],''.join(str(x) for x in range(n)))
                self.assertEqual(values[-1],''.join(str(x) for x in range(10-n,10)))
                self.assertEqual(values,sorted(set(values)))
                self.assertTrue(all(len(x)==n and all(x[i]<x[i+1] for i in range(n-1)) for x in values))
                self.assertFalse(raw.endswith(', '))
        cases=EXERCISES['c00/ex08']['cases']
        self.assertEqual([x[1] for x in cases[:9]],[str(x) for x in range(1,10)])
        self.assertNotIn('0',[x[1] for x in cases])
        self.assertNotIn('10',[x[1] for x in cases])

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class LastExerciseTests(unittest.TestCase):
    def run_sample(self, exercise, folder):
        with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
            return check_exercise(ROOT/folder,exercise)

    def run_bad(self, exercise, filename, code):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t); (p/filename).write_text(code)
            with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
                return check_exercise(p,exercise)

    def test_all_four_example_implementations_pass(self):
        for ex,folder in [('c00/ex05','ft_print_comb'),('c00/ex06','ft_print_comb2'),('c00/ex07','ft_putnbr'),('c00/ex08','ft_print_combn')]:
            with self.subTest(exercise=ex):
                report=self.run_sample(ex,folder)
                self.assertEqual(report['result'],'passed',report)
                self.assertEqual(report['exercise'],'42/c/'+ex)

    def test_ex06_two_full_outputs_not_truncated(self):
        report=self.run_sample('c00/ex06','ft_print_comb2')
        self.assertTrue(any(x['name']=='Test deux appels consécutifs' and x['status']=='pass' for x in report['checks']))

    def test_extremes_and_zero_for_putnbr(self):
        report=self.run_sample('c00/ex07','ft_putnbr')
        for label in ('Test int minimum','Test int maximum','Test nombre 0','Test trois appels consécutifs'):
            self.assertTrue(any(x['name']==label and x['status']=='pass' for x in report['checks']),label)
        self.assertLess(INT_MIN_PY,0); self.assertGreater(INT_MAX_PY,0)

    def test_truncated_or_wrong_implementations_fail(self):
        cases=[('c00/ex05','ft_print_comb.c','#include <unistd.h>\nvoid ft_print_comb(void) { write(1, "012", 3); }\n'),
               ('c00/ex06','ft_print_comb2.c','#include <unistd.h>\nvoid ft_print_comb2(void) { write(1, "00 01", 5); }\n'),
               ('c00/ex07','ft_putnbr.c','#include <unistd.h>\nvoid ft_putnbr(int n) { (void)n; write(1, "0", 1); }\n'),
               ('c00/ex08','ft_print_combn.c','#include <unistd.h>\nvoid ft_print_combn(int n) { (void)n; write(1, "01", 2); }\n')]
        for exercise,filename,code in cases:
            with self.subTest(exercise=exercise):
                report=self.run_bad(exercise,filename,code)
                self.assertEqual(report['result'],'failed')
                self.assertTrue(any(x['name'].startswith('Test ') and x['status']=='fail' for x in report['checks']))

    def test_bad_prototype_rejected_for_each_new_exercise(self):
        for exercise,name in [('c00/ex05','ft_print_comb'),('c00/ex06','ft_print_comb2')]:
            with self.subTest(exercise=exercise):
                report=self.run_bad(exercise,name+'.c',f'void {name}(int x) {{ (void)x; }}\n')
                self.assertTrue(any(x['name']=='Prototype' and x['status']=='fail' for x in report['checks']))
        for exercise,name in [('c00/ex07','ft_putnbr'),('c00/ex08','ft_print_combn')]:
            with self.subTest(exercise=exercise):
                report=self.run_bad(exercise,name+'.c',f'void {name}(unsigned int x) {{ (void)x; }}\n')
                self.assertTrue(any(x['name']=='Prototype' and x['status']=='fail' for x in report['checks']))

    def test_unsupported_integer_model_is_incomplete(self):
        spec=EXERCISES['c00/ex07']; original=spec['harness']
        with patch.dict(spec, {'harness': original.replace('_Static_assert(CHAR_BIT == 8', '_Static_assert(CHAR_BIT == 1')}):
            report=self.run_sample('c00/ex07','ft_putnbr')
        self.assertEqual(report['result'],'incomplete')
        self.assertTrue(any(x['name']=='Plateforme' and x['status']=='unavailable' for x in report['checks']))

class LastExerciseDispatchTests(unittest.TestCase):
    def test_cli_and_worker_dispatch_ex08(self):
        report={'result':'passed','checks':[],'exercise':'42/c/c00/ex08'}
        with patch('moulinette.cli.check_exercise',return_value=report) as checker, \
             contextlib.redirect_stdout(io.StringIO()):
            code=cli.main(['check','.','--exercise','c00/ex08','--unsafe-local','--no-history'])
        self.assertEqual(code,0); self.assertEqual(checker.call_args.args[1],'c00/ex08')
        parent,child=socket.socketpair(); results=[]
        state={'scope':'scope','pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
        def worker():
            with child: results.append(cgroup_worker.serve(child,'scope'))
        with parent, patch('moulinette.cgroup_worker.verify_current_scope',return_value=state), \
             patch('moulinette.cgroup_worker.check_exercise',return_value=dict(report)) as checker:
            parent.settimeout(2); thread=threading.Thread(target=worker); thread.start()
            self.assertEqual(receive_object(parent)['phase'],'ready')
            send_object(parent,{'action':'run','path':'/trusted','exercise':'c00/ex08'})
            self.assertEqual(receive_object(parent)['report']['exercise'],'42/c/c00/ex08'); thread.join(2)
        self.assertEqual(results,[0]); self.assertEqual(checker.call_args.args[1],'c00/ex08')

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

    def test_all_four_examples_in_real_bwrap_and_norminette(self):
        for exercise,folder in [('c00/ex05','ft_print_comb'),('c00/ex06','ft_print_comb2'),('c00/ex07','ft_putnbr'),('c00/ex08','ft_print_combn')]:
            with self.subTest(exercise=exercise):
                report=check_exercise(ROOT/folder,exercise,sandbox=True)
                self.assertEqual(report['result'],'passed',report)
                self.assertTrue(any(x['name']=='Norminette adaptée' and x['status']=='pass' for x in report['checks']))


class LastScopeFlowTests(unittest.TestCase):
    def test_simulated_scope_launcher_for_ex08(self):
        import subprocess
        from moulinette import cgroup_launcher
        base={'pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
        report=successful_report('c00/ex08')
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
            actual,error=cgroup_launcher.launch('/trusted','c00/ex08')
        self.assertIsNone(error)
        self.assertEqual(actual['exercise'],'42/c/c00/ex08')
        self.assertEqual(actual['result'],'passed')

if __name__ == '__main__':
    unittest.main()

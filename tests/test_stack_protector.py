"""Régressions : compilateur durci et ambiguïté d'origine du canari."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import checker

EXAMPLES = Path(__file__).resolve().parent.parent / 'exemples'

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class StackProtectorTests(unittest.TestCase):
    def test_explicit_stack_check_reference_remains_incomplete(self):
        source = (EXAMPLES/'ft_print_comb'/'ft_print_comb.c').read_text()
        source = 'extern void __stack_chk_fail(void);\n' + source.replace("\twrite(1, digits, 3);", "\tif (write(1, digits, 3) == -999) __stack_chk_fail();")
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'ft_print_comb.c').write_text(source)
            with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
                report=checker.check_exercise(Path(tmp),'c00/ex05')
        self.assertEqual(report['result'],'incomplete',report)
        symbols=next(x for x in report['checks'] if x['name']=='Fonctions externes')
        self.assertEqual(symbols['status'],'unavailable')
        self.assertIn('__stack_chk_fail',symbols['message'])

    def test_alternate_object_is_analysed_before_execution(self):
        import os
        cc=shutil.which('cc')
        # The compiler flag changes __SSP_ALL__; the fallback adds a forbidden
        # function. A validator that inspects only the original object would miss it.
        source = (EXAMPLES/'ft_print_comb'/'ft_print_comb.c').read_text()
        source = '#ifndef __SSP_ALL__\n#include <stdio.h>\n#endif\n' + source
        source = source.replace("\twrite(1, digits, 3);", "#ifndef __SSP_ALL__\n\tputs(\"bad\");\n#endif\n\twrite(1, digits, 3);")
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp); wrapper=tmp/'cc'
            wrapper.write_text('#!/bin/sh\nexec "'+cc+'" -fstack-protector-all "$@"\n'); wrapper.chmod(0o755)
            submission=tmp/'submission'; submission.mkdir()
            (submission/'ft_print_comb.c').write_text(source)
            with patch.dict(os.environ,{'PATH':str(tmp)+':'+os.environ['PATH']}), \
                 patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
                report=checker.check_exercise(submission,'c00/ex05')
        self.assertEqual(report['result'],'failed',report)
        self.assertTrue(any(x['name']=='Fonctions externes' and x['status']=='fail' and 'puts' in x['message'] for x in report['checks']))
        self.assertFalse(any(x['name'].startswith('Test ') for x in report['checks']))

    def test_failed_alternate_symbol_scan_stops_before_linking(self):
        import os
        real_run=checker._run; calls=[]; cc=shutil.which('cc')
        def run(cmd,*args,**kwargs):
            calls.append(cmd)
            if '-u' in cmd and 'submission-nocanary.o' in cmd:
                return (1,b'',b'nm failed',False)
            return real_run(cmd,*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp:
            wrapper=Path(tmp)/'cc'; wrapper.write_text('#!/bin/sh\nexec "'+cc+'" -fstack-protector-all "$@"\n'); wrapper.chmod(0o755)
            with patch.dict(os.environ,{'PATH':tmp+':'+os.environ['PATH']}), \
                 patch('moulinette.checker._run',side_effect=run), \
                 patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
                report=checker.check_exercise(EXAMPLES/'ft_print_comb','c00/ex05')
        self.assertEqual(report['result'],'incomplete',report)
        self.assertFalse(any(x['name']=='Adaptation compilation' for x in report['checks']))
        links=[x for x in calls if 'harness.c' in x]
        self.assertEqual(links, [])  # pas de liaison si l'origine du symbole reste indéterminée

    def test_failed_alternate_stops_before_linking(self):
        import os
        real_run=checker._run; calls=[]; cc=shutil.which('cc')
        def run(cmd,*args,**kwargs):
            calls.append(cmd)
            if 'submission-nocanary.o' in cmd and '-c' in cmd:
                return (1,b'',b'alternate compilation failed',False)
            return real_run(cmd,*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp:
            wrapper=Path(tmp)/'cc'; wrapper.write_text('#!/bin/sh\nexec "'+cc+'" -fstack-protector-all "$@"\n'); wrapper.chmod(0o755)
            with patch.dict(os.environ,{'PATH':tmp+':'+os.environ['PATH']}), \
                 patch('moulinette.checker._run',side_effect=run), \
                 patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
                report=checker.check_exercise(EXAMPLES/'ft_print_comb','c00/ex05')
        self.assertEqual(report['result'],'incomplete',report)
        self.assertTrue(any('submission-nocanary.o' in x and '-c' in x for x in calls))
        links=[x for x in calls if 'harness.c' in x]
        self.assertEqual(links, [])  # pas de liaison si l'origine du symbole reste indéterminée

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm') and shutil.which('norminette'), 'bwrap, cc, nm et norminette requis')
class HardenedCompilerSandboxTests(unittest.TestCase):
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

    def test_examples_with_hardened_compiler_and_real_bwrap(self):
        real_run=checker._run
        for ex,folder in [('c00/ex05','ft_print_comb'),('c00/ex06','ft_print_comb2'),('c00/ex07','ft_putnbr'),('c00/ex08','ft_print_combn')]:
            with self.subTest(exercise=ex):
                calls=[]
                def run(cmd,*args,**kwargs):
                    # Imite un compilateur système qui active la protection par défaut.
                    cmd=list(cmd)
                    if '-fno-builtin' in cmd: cmd.insert(cmd.index('-fno-builtin'),'-fstack-protector-all')
                    calls.append(cmd)
                    return real_run(cmd,*args,**kwargs)
                with patch('moulinette.checker._run',side_effect=run):
                    report=checker.check_exercise(EXAMPLES/folder,ex,sandbox=True)
                self.assertEqual(report['result'],'passed',report)
                self.assertTrue(any(x['name']=='Adaptation compilation' and '-fno-stack-protector' in x['message'] for x in report['checks']))
                self.assertTrue(any(x['name']=='Norminette adaptée' and x['status']=='pass' for x in report['checks']))
                nm_alt=[x for x in calls if '-u' in x and 'submission-nocanary.o' in x]
                link_alt=[x for x in calls if 'harness.c' in x and 'submission-nocanary.o' in x]
                self.assertEqual(len(nm_alt),1); self.assertEqual(len(link_alt),1)

    def test_simulated_scope_with_real_bwrap_and_hardened_compiler(self):
        import subprocess, threading
        from moulinette import cgroup_launcher, cgroup_worker
        base={'pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
        class FakeProcess:
            def __init__(self,cmd,**kwargs):
                scope=next(x.split('=',1)[1] for x in cmd if x.startswith('--unit='))
                sockpath=cmd[cmd.index('--socket')+1]; self.code=None; self.pid=999999
                state=dict(base,scope=scope,group='/user.slice/'+scope)
                def worker():
                    with patch('moulinette.cgroup_worker.verify_current_scope',return_value=state):
                        self.code=cgroup_worker.main(['--socket',sockpath,'--scope',scope])
                self.thread=threading.Thread(target=worker); self.thread.start()
            def poll(self): return self.code
            def wait(self,timeout=None):
                self.thread.join(timeout)
                if self.thread.is_alive(): raise subprocess.TimeoutExpired('fake',timeout)
                return self.code
        def gate(scope,**kwargs): return dict(base,scope=scope,group='/user.slice/'+scope)
        real_run=checker._run
        def hardened_run(cmd,*args,**kwargs):
            cmd=list(cmd)
            if '-fno-builtin' in cmd: cmd.insert(cmd.index('-fno-builtin'),'-fstack-protector-all')
            return real_run(cmd,*args,**kwargs)
        real_popen=subprocess.Popen
        def popen(cmd,*args,**kwargs):
            if cmd and '--scope' in cmd and '--user' in cmd: return FakeProcess(cmd,*args,**kwargs)
            return real_popen(cmd,*args,**kwargs)
        with patch('moulinette.cgroup_launcher.subprocess.Popen',side_effect=popen), \
             patch('moulinette.cgroup_launcher.verify_current_scope',side_effect=gate), \
             patch('moulinette.cgroup_launcher._events',side_effect=[1,0]), \
             patch('moulinette.cgroup_launcher._stop'), \
             patch('moulinette.checker._run',side_effect=hardened_run):
            report,error=cgroup_launcher.launch(EXAMPLES/'ft_print_comb','c00/ex05')
        self.assertIsNone(error)
        self.assertEqual(report['result'],'passed',report)
        self.assertTrue(any(x['name']=='Adaptation compilation' for x in report['checks']))

if __name__=='__main__': unittest.main()

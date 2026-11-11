"""Régressions des constats de l'audit v0.15 ; aucune sonde destructive."""
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import checker, cgroup_launcher, cgroup_worker
from moulinette.scope_protocol import receive_object, send_object, ScopeProtocolError
from support_audit import successful_report

EXAMPLE=Path(__file__).resolve().parent.parent/'exemples'/'ft_putchar'

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class SymbolsFailClosedTests(unittest.TestCase):
    def run_forged_nm(self, stdout, stderr=b''):
        commands=[]; real_run=checker._run
        def run(cmd,*args,**kwargs):
            commands.append(cmd)
            if len(cmd)>1 and cmd[1]=='-u': return (0,stdout,stderr,False)
            return real_run(cmd,*args,**kwargs)
        with patch('moulinette.checker._run',side_effect=run):
            report=checker.check_exercise(EXAMPLE,'c00/ex00')
        return report,commands

    def test_forbidden_symbol_stops_before_link_and_test(self):
        report,calls=self.run_forged_nm(b' U write\n U puts\n')
        self.assertEqual(report['result'],'failed')
        self.assertTrue(any(x['name']=='Fonctions externes' and x['status']=='fail' for x in report['checks']))
        self.assertFalse(any('harness.c' in cmd or 'test-ex00' in cmd[0] for cmd in calls))

    def test_unresolved_stack_symbol_stops_before_link_and_test(self):
        report,calls=self.run_forged_nm(b' U write\n U __stack_chk_fail\n')
        self.assertEqual(report['result'],'incomplete')
        self.assertFalse(any('harness.c' in cmd or 'test-ex00' in cmd[0] for cmd in calls))
        self.assertTrue(any('submission-nocanary.o' in cmd for cmd in calls))

    def test_warning_on_stderr_does_not_validate_empty_output(self):
        report,calls=self.run_forged_nm(b'',b'nm: warning\n')
        self.assertEqual(report['result'],'incomplete')
        self.assertFalse(any('harness.c' in cmd for cmd in calls))

    def test_versioned_symbol_not_shortened_to_write(self):
        report,calls=self.run_forged_nm(b' U write@unexpected\n')
        self.assertEqual(report['result'],'incomplete')
        self.assertFalse(any('harness.c' in cmd for cmd in calls))

    def test_stack_guard_is_ambiguous_not_automatic_student_failure(self):
        report,calls=self.run_forged_nm(b' U write\n U __stack_chk_guard\n')
        self.assertEqual(report['result'],'incomplete')
        self.assertTrue(any('submission-nocanary.o' in cmd for cmd in calls))
        self.assertFalse(any('harness.c' in cmd for cmd in calls))

    def test_generated_stack_guard_can_be_recompiled_and_reanalysed(self):
        calls=[]; outputs=iter([b' U write\n U __stack_chk_guard\n',b' U write\n'])
        real_run=checker._run
        def run(cmd,*args,**kwargs):
            calls.append(cmd)
            if len(cmd)>1 and cmd[1]=='-u': return (0,next(outputs),b'',False)
            return real_run(cmd,*args,**kwargs)
        with patch('moulinette.checker._run',side_effect=run), patch('moulinette.checker.check_norm',return_value=('pass','simulé')):
            report=checker.check_exercise(EXAMPLE,'c00/ex00')
        self.assertEqual(report['result'],'passed',report)
        self.assertTrue(any('submission-nocanary.o' in cmd and 'harness.c' in cmd for cmd in calls))
        self.assertTrue(any(x['name']=='Adaptation compilation' for x in report['checks']))

    def test_missing_nm_stops_local_before_link_and_test(self):
        real_which=shutil.which; real_run=checker._run; calls=[]
        def which(name): return None if name=='nm' else real_which(name)
        def run(cmd,*args,**kwargs): calls.append(cmd); return real_run(cmd,*args,**kwargs)
        with patch('moulinette.checker.shutil.which',side_effect=which), patch('moulinette.checker._run',side_effect=run):
            report=checker.check_exercise(EXAMPLE,'c00/ex00')
        self.assertEqual(report['result'],'incomplete')
        self.assertFalse(any('harness.c' in cmd or 'test-ex00' in cmd[0] for cmd in calls))

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap et outils C requis')
class SandboxSymbolAuditTests(unittest.TestCase):
    def test_real_forbidden_symbol_stops_before_any_link_or_execution(self):
        from moulinette.sandbox_doctor import diagnose
        relevant=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not relevant or any(x['status']!='pass' for x in relevant): raise unittest.SkipTest('Bubblewrap indisponible')
        actual=checker.ExperimentalRunner; actions=[]
        class RecordingRunner:
            def __init__(self,*args,**kwargs): self.delegate=actual(*args,**kwargs)
            def __call__(self,cmd,*args,**kwargs):
                actions.append(cmd)
                return self.delegate(cmd,*args,**kwargs)
        with tempfile.TemporaryDirectory() as t:
            path=Path(t); (path/'ft_putchar.c').write_text('#include <stdio.h>\nvoid ft_putchar(char c) { putchar(c); }\n')
            with patch('moulinette.checker.ExperimentalRunner',RecordingRunner):
                report=checker.check_exercise(path,'c00/ex00',sandbox=True)
        self.assertEqual(report['result'],'failed',report)
        self.assertTrue(any(x['name']=='Fonctions externes' and x['status']=='fail' for x in report['checks']))
        self.assertFalse(any('harness.c' in cmd or 'test-ex00' in cmd[0] for cmd in actions))

@unittest.skipUnless(shutil.which('bwrap'), 'bwrap requis')
class NormVenvAuditTests(unittest.TestCase):
    def test_parent_of_home_and_symlinked_config_rejected_before_mount(self):
        from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); home=root/'homes'/'alice'; home.mkdir(parents=True)
            broad=home.parent; (broad/'bin').mkdir(); (broad/'bin'/'norminette').write_text('')
            (broad/'bin'/'python').write_text(''); (broad/'pyvenv.cfg').write_text('home=foo')
            original=shutil.which
            def which(n): return str(broad/'bin'/'norminette') if n=='norminette' else original(n)
            with patch('moulinette.sandbox_runner.Path.home',return_value=home), \
                 patch('moulinette.sandbox_runner.shutil.which',side_effect=which):
                runner=ExperimentalRunner(lambda *args,**kwargs:self.fail('ne doit pas lancer bwrap'))
                with self.assertRaises(SandboxUnavailable): runner([str(broad/'bin'/'norminette'),'--version'],root,5)
            dedicated=root/'dedicated'; (dedicated/'bin').mkdir(parents=True)
            (dedicated/'bin'/'norminette').write_text(''); (dedicated/'bin'/'python').write_text('')
            (dedicated/'pyvenv.cfg').symlink_to(broad/'pyvenv.cfg')
            def which2(n): return str(dedicated/'bin'/'norminette') if n=='norminette' else original(n)
            with patch('moulinette.sandbox_runner.Path.home',return_value=home), \
                 patch('moulinette.sandbox_runner.shutil.which',side_effect=which2):
                runner=ExperimentalRunner(lambda *args,**kwargs:self.fail('ne doit pas lancer bwrap'))
                with self.assertRaises(SandboxUnavailable): runner([str(dedicated/'bin'/'norminette'),'--version'],root,5)

class ScopeAuditTests(unittest.TestCase):
    def test_real_socket_peer_identity_is_checked(self):
        a,b=socket.socketpair()
        with a,b:
            self.assertEqual(cgroup_launcher._peer_identity(a), os.getpid())

    def test_nonmatching_uid_is_rejected(self):
        import struct
        class Sock:
            def getsockopt(self,*args): return struct.pack('iII',os.getpid(),(os.getuid()+1) % (2**32),os.getgid())
        with self.assertRaises(ScopeProtocolError): cgroup_launcher._peer_identity(Sock())

    def test_mismatched_socket_pid_and_missing_report_checks_are_rejected(self):
        base={'pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
        def run_fake(report, wrong_pid=False):
            seen=[]; launch_kwargs=[]
            class Process:
                def __init__(self,cmd,**kwargs):
                    launch_kwargs.append(kwargs)
                    scope=next(x.split('=',1)[1] for x in cmd if x.startswith('--unit=')); path=cmd[cmd.index('--socket')+1]
                    self.code=None; self.pid=999999
                    def run():
                        try:
                            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
                                sock.connect(path); sock.settimeout(3)
                                send_object(sock,{'phase':'ready','pid':os.getpid()+(1 if wrong_pid else 0),'scope':scope})
                                try: req=receive_object(sock)
                                except ScopeProtocolError: self.code=0; return
                                seen.append(req)
                                item=dict(report, cgroup_limits=dict(base,swap_max=0))
                                send_object(sock,{'phase':'result','report':item})
                                self.code=0
                        except (OSError,ScopeProtocolError): self.code=0
                    self.thread=threading.Thread(target=run); self.thread.start()
                def poll(self): return self.code
                def wait(self,timeout=None):
                    self.thread.join(timeout)
                    if self.thread.is_alive(): raise subprocess.TimeoutExpired('fake',timeout)
                    return self.code
            def gate(scope,**kwargs): return dict(base,scope=scope,group='/user.slice/'+scope)
            with patch('moulinette.cgroup_launcher.shutil.which',side_effect=lambda n:'/usr/bin/'+n), \
                 patch('moulinette.cgroup_launcher.subprocess.Popen',Process), \
                 patch('moulinette.cgroup_launcher.verify_current_scope',side_effect=gate), \
                 patch('moulinette.cgroup_launcher._events',return_value=1), \
                 patch('moulinette.cgroup_launcher._stop'), \
                 patch('moulinette.cgroup_launcher._wait_unpopulated',return_value=True):
                actual,error=cgroup_launcher.launch('/trusted','c00/ex00')
            return actual,error,seen,launch_kwargs
        report=successful_report('c00/ex00')
        actual,error,seen,kwargs=run_fake(report,wrong_pid=True)
        self.assertIsNone(actual); self.assertIn('PID déclaré',error); self.assertEqual(seen,[])
        self.assertEqual(kwargs[0]['stdout'],subprocess.DEVNULL); self.assertEqual(kwargs[0]['stderr'],subprocess.DEVNULL)
        for checks in ([],[{'name':'Compilation','status':'pass','message':'ok'}],
                       [x for x in report['checks'] if x['name']!='Norminette adaptée']):
            actual,error,seen,_=run_fake(dict(report,checks=checks))
            self.assertIsNone(actual); self.assertIn('contrôles obligatoires',error)
            self.assertEqual(len(seen),1)

    def test_early_failure_explicitly_reports_unconfirmed_cleanup(self):
        class Fake:
            pid=999999
            def __init__(self,*args,**kwargs): pass
            def poll(self): return 0
            def wait(self,timeout=None): return 0
        with patch('moulinette.cgroup_launcher.shutil.which',side_effect=lambda n:'/usr/bin/'+n), \
             patch('moulinette.cgroup_launcher.subprocess.Popen',Fake), \
             patch('moulinette.cgroup_launcher._accept_or_exit',side_effect=ScopeProtocolError('interruption')), \
             patch('moulinette.cgroup_launcher._stop') as stop:
            report,error=cgroup_launcher.launch('/trusted','c00/ex00')
        self.assertIsNone(report); self.assertIn('Nettoyage du cgroup non confirmé',error)
        self.assertEqual(stop.call_count,1)

    def test_cleanup_wait_converges_or_fails_closed(self):
        with patch('moulinette.cgroup_launcher._events',side_effect=[1,1,0]), patch('moulinette.cgroup_launcher.time.sleep'):
            self.assertTrue(cgroup_launcher._wait_unpopulated(Path('/dummy')))
        with patch('moulinette.cgroup_launcher._events',return_value=1):
            self.assertFalse(cgroup_launcher._wait_unpopulated(Path('/dummy'),timeout=0))
        with patch('moulinette.cgroup_launcher._events',return_value=None):
            self.assertFalse(cgroup_launcher._wait_unpopulated(Path('/dummy')))

    def test_sigterm_during_launch_calls_scope_stop(self):
        script = r"""import os, socket, subprocess, threading
from unittest.mock import patch
from moulinette import cgroup_launcher as L
from moulinette.scope_protocol import send_object,receive_object
base={'pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}
class Fake:
 def __init__(self,cmd,**kwargs):
  self.pid=999999
  scope=next(x.split('=',1)[1] for x in cmd if x.startswith('--unit=')); path=cmd[cmd.index('--socket')+1]
  def worker():
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
    sock.connect(path); send_object(sock,{'phase':'ready','pid':os.getpid(),'scope':scope}); receive_object(sock)
    print('worker_started',flush=True)
    try: sock.recv(1)
    except OSError: pass
  threading.Thread(target=worker,daemon=True).start()
 def poll(self): return 0
 def wait(self,timeout=None): return 0
def gate(scope,**kwargs): return dict(base,scope=scope,group='/user.slice/'+scope)
def stop(*args): print('stop_called',flush=True)
with patch('moulinette.cgroup_launcher.shutil.which',side_effect=lambda n:'/usr/bin/'+n), patch('moulinette.cgroup_launcher.subprocess.Popen',Fake), patch('moulinette.cgroup_launcher.verify_current_scope',side_effect=gate), patch('moulinette.cgroup_launcher._events',return_value=1), patch('moulinette.cgroup_launcher._stop',side_effect=stop), patch('moulinette.cgroup_launcher._wait_unpopulated',return_value=True):
 report,error=L.launch('/trusted','c00/ex00')
 print('finished',error,flush=True)
"""
        proc=subprocess.Popen([sys.executable,'-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(),'worker_started')
            proc.send_signal(signal.SIGTERM)
            out,err=proc.communicate(timeout=5)
        finally:
            if proc.poll() is None: proc.kill(); proc.wait()
        self.assertEqual(proc.returncode,0,err)
        self.assertIn('stop_called',out); self.assertIn('Correction interrompue',out)

    def test_sigterm_is_catchable_and_handlers_restored(self):
        script = '''import signal,time\nfrom moulinette.cgroup_launcher import _termination_signals\nold=signal.getsignal(signal.SIGTERM)\ntry:\n  with _termination_signals():\n    print("ready",flush=True)\n    time.sleep(5)\nexcept KeyboardInterrupt:\n  print("handled",flush=True)\nprint("restored",signal.getsignal(signal.SIGTERM)==old,flush=True)\n'''
        proc=subprocess.Popen([sys.executable,'-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(),'ready')
            proc.send_signal(signal.SIGTERM)
            out,err=proc.communicate(timeout=5)
        finally:
            if proc.poll() is None: proc.kill(); proc.wait()
        self.assertEqual(proc.returncode,0,err)
        self.assertIn('handled',out); self.assertIn('restored True',out)

if __name__=='__main__': unittest.main()

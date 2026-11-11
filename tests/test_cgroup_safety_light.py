"""Témoins légers et simulations. Sans OOM, boucle active ou saturation."""
import os
import resource
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette.cgroup_launcher import _events, _wait_unpopulated
from moulinette.checker import _run


class ScopeEventTests(unittest.TestCase):
    def test_present_scope_without_events_is_unknown_not_empty(self):
        with tempfile.TemporaryDirectory() as t:
            scope=Path(t)/'scope';scope.mkdir()
            self.assertIsNone(_events(scope))
            self.assertFalse(_wait_unpopulated(scope,timeout=0))

    def test_missing_scope_with_present_parent_is_empty(self):
        with tempfile.TemporaryDirectory() as t:
            scope=Path(t)/'scope'
            self.assertEqual(_events(scope),0)

    def test_missing_parent_is_unknown(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(_events(Path(t)/'missing'/'scope'))

    def test_valid_invalid_and_unreadable_state(self):
        with tempfile.TemporaryDirectory() as t:
            scope=Path(t);f=scope/'cgroup.events'
            for data,expected in [('populated 1\n',1),('populated 0\n',0),
                                  ('populated 1\npopulated 0\n',None),('populated x\n',None)]:
                f.write_text(data);self.assertEqual(_events(scope),expected)
            with patch.object(Path,'read_text',side_effect=PermissionError('simulation')):
                self.assertIsNone(_events(scope))

    def test_lstat_failure_cannot_be_reported_empty(self):
        with tempfile.TemporaryDirectory() as t:
            scope=Path(t)/'scope';scope.mkdir()
            with patch.object(Path,'lstat',side_effect=PermissionError('simulation')):
                self.assertIsNone(_events(scope))



class LimitConfigurationTests(unittest.TestCase):
    def test_project_rlimits_declared_without_allocating_resources(self):
        from moulinette.project_engine import _limits
        with patch('moulinette.project_engine.resource.setrlimit') as setter:
            _limits()
        limits=dict(call.args for call in setter.call_args_list)
        self.assertEqual(limits[resource.RLIMIT_CPU],(90,90))
        self.assertEqual(limits[resource.RLIMIT_AS],(1024**3,1024**3))
        self.assertEqual(limits[resource.RLIMIT_FSIZE],(16*1024**2,16*1024**2))
        self.assertEqual(limits[resource.RLIMIT_CORE],(0,0))

    def test_single_file_rlimits_declared_without_running_program(self):
        from moulinette import checker
        for limited,expected in [(True,((2,3),256*1024**2,1024**2)),
                                 (False,((10,11),1024**3,16*1024**2))]:
            with self.subTest(limited=limited):
                def fake(cmd,cwd,timeout,env,setup,**kwargs):
                    setup();return 0,b'',b'',False
                with patch.object(checker,'run_bounded',side_effect=fake), \
                     patch.object(checker.resource,'setrlimit') as setter:
                    checker._run(['fixture'],Path('/tmp'),1,limited=limited)
                limits=dict(call.args for call in setter.call_args_list)
                self.assertEqual(limits[resource.RLIMIT_CPU],expected[0])
                self.assertEqual(limits[resource.RLIMIT_AS],(expected[1],expected[1]))
                self.assertEqual(limits[resource.RLIMIT_FSIZE],(expected[2],expected[2]))
                self.assertEqual(limits[resource.RLIMIT_CORE],(0,0))

@unittest.skipUnless(hasattr(os,'fork') and sys.platform.startswith('linux'),'Linux fork requis')
class CleanupWitnessTests(unittest.TestCase):
    def _not_running(self,pid):
        try:
            state=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1][0]
        except FileNotFoundError:
            return True
        return state=='Z'

    def test_timeout_kills_a_sleeping_child_in_same_group(self):
        script=('import os,time\n'
                'p=os.fork()\n'
                'if p==0: time.sleep(3);os._exit(0)\n'
                'os.write(1,(str(p)+"\\n").encode());time.sleep(3)\n')
        code,out,err,timed=_run([sys.executable,'-c',script],Path('/tmp'),0.3)
        self.assertTrue(timed,(code,out,err));pid=int(out.strip())
        self.assertTrue(self._not_running(pid),'Le descendant du témoin semble encore actif.')

    def test_sigterm_interrupts_capture_and_stops_group(self):
        # Un témoin de sommeil auto-terminant ; le signal vise uniquement
        # le superviseur enfant créé pour ce test, jamais un PID externe.
        with tempfile.TemporaryDirectory() as t:
            marker=Path(t)/'child-pid'
            child=('import os,sys,time\n'
                   'with open(sys.argv[1]+".tmp","w") as f: f.write(str(os.getpid()))\n'
                   'os.replace(sys.argv[1]+".tmp",sys.argv[1])\n'
                   'time.sleep(4)\n')
            driver=('import sys\n'
                    'from moulinette.process_capture import run_bounded\n'
                    'from moulinette.cgroup_launcher import _termination_signals\n'
                    'try:\n'
                    ' with _termination_signals():\n'
                    '  run_bounded([sys.executable,"-c",sys.argv[1],sys.argv[2]],"/tmp",6,{},lambda:None)\n'
                    'except KeyboardInterrupt:\n'
                    ' print("interrupted",flush=True)\n')
            p=subprocess.Popen([sys.executable,'-c',driver,child,str(marker)],
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                deadline=time.monotonic()+3
                while time.monotonic()<deadline and not marker.exists() and p.poll() is None:
                    time.sleep(0.02)
                self.assertTrue(marker.exists(),'Témoin non démarré')
                pid=int(marker.read_text())
                p.send_signal(signal.SIGTERM)
                out,err=p.communicate(timeout=3)
                self.assertEqual(p.returncode,0,err)
                self.assertIn(b'interrupted',out)
                self.assertTrue(self._not_running(pid),'Le processus du témoin semble encore actif.')
            finally:
                if p.poll() is None:p.kill();p.wait(timeout=3)

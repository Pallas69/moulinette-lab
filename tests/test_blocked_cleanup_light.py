"""Témoins légers : sommeil borné et simulations, sans charge ni OOM."""
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import project_job
from moulinette.scope_protocol import ScopeProtocolError, receive_object

@unittest.skipUnless(sys.platform.startswith('linux') and hasattr(os,'fork'),'Linux requis')
class ProjectCommandCleanupTests(unittest.TestCase):
    def run_isolated(self,script,timeout):
        with tempfile.TemporaryDirectory() as t, patch.object(project_job,'ISOLATED_JOB',True):
            return project_job.execute([sys.executable,'-c',script],t,timeout=timeout)

    def assert_stopped(self,pid):
        deadline=time.monotonic()+1
        while time.monotonic()<deadline:
            try: state=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1][0]
            except FileNotFoundError:return
            if state=='Z':return
            time.sleep(.01)
        self.fail('Descendant témoin encore actif')

    def test_timeout_stops_same_group_descendant_before_return(self):
        script=('import os,time\n'
                'p=os.fork()\n'
                'if not p: time.sleep(2);os._exit(0)\n'
                'os.write(1,(str(p)+"\\n").encode());time.sleep(2)\n')
        result=self.run_isolated(script,.25)
        self.assertTrue(result['timeout'],result)
        self.assertFalse(result['unavailable']);self.assert_stopped(int(result['out'].strip()))

    def test_normal_exit_stops_same_group_descendant_before_return(self):
        script=('import os,time\n'
                'p=os.fork()\n'
                'if not p: time.sleep(2);os._exit(0)\n'
                'os.write(1,(str(p)+"\\n").encode());os._exit(0)\n')
        result=self.run_isolated(script,1)
        self.assertFalse(result['timeout'],result);self.assertEqual(result['code'],0)
        self.assert_stopped(int(result['out'].strip()))

    def test_cleanup_failure_is_not_reported_as_success(self):
        with patch.object(project_job.os,'killpg',side_effect=PermissionError('simulation')):
            with self.assertRaisesRegex(project_job.CleanupUnconfirmed,'Arrêt du groupe impossible'):
                self.run_isolated('pass',1)

    def test_unknown_process_state_never_signals_a_reused_pid(self):
        from unittest.mock import MagicMock
        read_fd,write_fd=os.pipe();os.close(read_fd)
        fake=MagicMock(pid=987654,stdin=os.fdopen(write_fd,'wb',buffering=0),returncode=0)
        try:
            with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err, \
                 patch.object(project_job.subprocess,'Popen',return_value=fake), \
                 patch.object(project_job.os,'waitid',side_effect=ChildProcessError), \
                 patch.object(project_job.os,'killpg') as kill:
                with self.assertRaisesRegex(project_job.CleanupUnconfirmed,'État du processus perdu'):
                    project_job._execute_isolated(['fixture'],'/tmp',b'',1,out,err)
            kill.assert_not_called()
        finally:
            if not fake.stdin.closed:fake.stdin.close()

    def test_unreadable_proc_does_not_count_as_empty(self):
        with patch.object(project_job.os,'scandir',side_effect=PermissionError('simulation')):
            with self.assertRaisesRegex(project_job.CleanupUnconfirmed,'Observation du groupe impossible'):
                project_job._wait_group_quiet(999)

    def test_stdin_is_still_a_pipe_and_binary_is_preserved(self):
        script='import os,stat\nassert stat.S_ISFIFO(os.fstat(0).st_mode)\nwhile True:\n b=os.read(0,4096)\n if not b: break\n os.write(1,b)\n'
        with tempfile.TemporaryDirectory() as t, patch.object(project_job,'ISOLATED_JOB',True):
            r=project_job.execute([sys.executable,'-c',script],t,stdin=b'a\x00b\xff',timeout=1)
        self.assertEqual((r['code'],r['out'],r['timeout']),(0,b'a\x00b\xff',False))

class AbortTests(unittest.TestCase):
    def test_timeout_does_not_run_next_test_or_norminette(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);inp=base/'input';inp.mkdir();work=base/'work';work.mkdir();(inp/'prog').write_text('fixture')
            cfg={'build':'script','script':'script.sh','binary':'prog','require_objects':False,
                 'skip_external_inspection':True,'style_files':['prog'],
                 'cases':[{'label':'bloqué','expected':''},{'label':'pas exécuté','expected':''}]}
            spec=base/'spec.json';spec.write_text(json.dumps(cfg))
            def execute(cmd,*args,**kwargs):
                if cmd[0]=='/bin/sh':return {'code':0,'out':b'','err':b'','timeout':False,'unavailable':False}
                return {'code':-9,'out':b'','err':b'','timeout':True,'unavailable':False}
            with patch.object(sys,'argv',['job',str(inp),str(work),str(spec)]), patch.object(project_job,'execute',side_effect=execute) as run:
                result=project_job.main()
            self.assertEqual(run.call_count,2)
            self.assertEqual(result['checks'][-1]['status'],'unavailable')
            self.assertIn('Délai dépassé',result['checks'][-1]['message'])
            self.assertEqual(result['styles'],[])

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'), 'Bubblewrap et compilateur requis')
class BubblewrapWitnessTests(unittest.TestCase):
    def test_blocked_project_aborts_in_real_bwrap(self):
        from moulinette.sandbox_doctor import diagnose
        from moulinette.project_engine import evaluate_project
        relevant=[c for c in diagnose()['checks'] if c['name']!='Limites et protection']
        if not relevant or any(c['status']!='pass' for c in relevant):
            self.skipTest('Bubblewrap non disponible')
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t)
            (folder/'build.sh').write_text('chmod +x prog\n')
            (folder/'prog').write_text('#!/bin/sh\nsleep 2 &\necho $!\nsleep 2\n')
            spec={'subject_version':'fixture','project':{'build':'script','script':'build.sh',
                  'binary':'prog','require_objects':False,'skip_external_inspection':True,
                  'cases':[{'label':'bloqué','expected':b'','timeout':.2},
                           {'label':'pas exécuté','expected':b''}]}}
            result=evaluate_project(folder,'c00/ex00',spec,sandbox=True)
        names=[c['name'] for c in result['checks']]
        self.assertEqual(result['result'],'incomplete',result)
        self.assertIn('Test bloqué',names)
        self.assertNotIn('Test pas exécuté',names)
        self.assertTrue(any('Délai dépassé' in c['message'] for c in result['checks']),result)

class DeadlineTests(unittest.TestCase):
    def test_deadline_applies_across_all_fragments(self):
        import struct
        class SlowFragments:
            def __init__(self):self.parts=[struct.pack('!I',2),b'{',b'}'];self.timeouts=[]
            def settimeout(self,value):self.timeouts.append(value)
            def recv(self,n):return self.parts.pop(0)
        fake=SlowFragments()
        with patch('moulinette.scope_protocol.time.monotonic',side_effect=[10,10.6,11.1]):
            with self.assertRaisesRegex(ScopeProtocolError,'global'):
                receive_object(fake,deadline=11)
        self.assertEqual(len(fake.timeouts),2)
        self.assertGreater(fake.timeouts[0],fake.timeouts[1])

if __name__=='__main__':unittest.main()

"""Régressions ciblées d'après la revue indépendante v0.21 ; aucun OOM."""
import contextlib
import io
import json
import os
import select
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette import cli
from moulinette.github_bounded import _parse_snapshot
from moulinette.github_source import GitHubSourceError, normalize_subdir
from moulinette.history import HistoryError, data_directory, read_history
from moulinette.dashboard import write_dashboard
from moulinette.cgroup_launcher import _validate_favorable_checks, _required_passes
from moulinette.scope_protocol import ScopeProtocolError
from moulinette.sandbox_runner import ExperimentalRunner, SandboxUnavailable

class GitEncodingTests(unittest.TestCase):
    def test_worker_payload_rejects_non_utf8_filename(self):
        obj={'version':1,'entries':['ft_putchar.c','bad\udcff.c'], 'source_type':'file','source_b64':'',
             'source':{'kind':'github','url':'https://github.com/a/b','commit':'1'*40,'ref':'main','subdir':'.'}}
        with self.assertRaises(GitHubSourceError):
            _parse_snapshot(obj,'https://github.com/a/b','main','.','ft_putchar.c')
    def test_git_subdir_rejects_surrogate_but_allows_utf8(self):
        with self.assertRaises(GitHubSourceError):normalize_subdir('français-\udcff')
        self.assertEqual(normalize_subdir('école/ex00'),('école','ex00'))
    def test_local_non_utf8_filename_report_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'code';folder.mkdir();(folder/'ft_putchar.c').write_text('void ft_putchar(char c){}')
            fd=os.open(os.fsencode(folder)+b'/fran\xc3\xa7ais-\xff',os.O_CREAT|os.O_WRONLY,0o600);os.close(fd)
            output=io.StringIO()
            with patch.dict(os.environ,{'XDG_DATA_HOME':tmp}),contextlib.redirect_stdout(output):
                status=cli.main(['check',str(folder),'--exercise','c00/ex00','--unsafe-local','--json'])
                history=read_history()
            self.assertEqual(status,1);report=json.loads(output.getvalue())
            msg=report['checks'][0]['message'];msg.encode('utf-8','strict')
            self.assertIn('français-',msg);self.assertIn('\\udcff',msg)
            self.assertEqual(history['count'],1)

class SqliteSidecarTests(unittest.TestCase):
    def test_existing_sidecars_with_symlink_or_hardlink_are_rejected(self):
        for suffix in ('-journal','-wal','-shm'):
            for kind in ('symlink','hardlink'):
                with self.subTest(suffix=suffix,kind=kind),tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_DATA_HOME':tmp}):
                    d=data_directory();d.mkdir();target=Path(tmp)/'victim';target.write_bytes(b'sentinel')
                    side=d/('history.sqlite3'+suffix)
                    if kind=='symlink':side.symlink_to(target)
                    else:os.link(target,side)
                    with self.assertRaises(HistoryError):read_history()
                    self.assertEqual(target.read_bytes(),b'sentinel')

class DashboardCleanupTests(unittest.TestCase):
    def test_fdopen_failure_closes_descriptor_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'XDG_DATA_HOME':tmp}):
            read_history(); seen=[]
            def fail(fd,*a,**k): seen.append(fd);raise OSError('fdopen failure')
            with patch('moulinette.dashboard.os.fdopen',side_effect=fail),self.assertRaises(OSError):write_dashboard()
            self.assertEqual(len(seen),1)
            with self.assertRaises(OSError):os.fstat(seen[0])
            self.assertEqual(list(data_directory().glob('.dashboard-*.html')),[])

class ReportsTests(unittest.TestCase):
    def test_unknown_pass_info_and_duplicate_singletons_are_rejected(self):
        checks=[{'name':x,'status':'pass'} for x in _required_passes('c00/ex00')]+[{'name':'Fonctions externes','status':'info'}]
        for extra in ([{'name':'Aucun contrôle connu','status':'pass'}],
                      [{'name':'Aucune info connue','status':'info'}],
                      [{'name':'Limites','status':'info'},{'name':'Limites','status':'info'}]):
            with self.subTest(extra=extra),self.assertRaises(ScopeProtocolError):_validate_favorable_checks('c00/ex00',checks+extra)
        _validate_favorable_checks('c00/ex00',checks+[{'name':'Sortie stderr','status':'info'}]*2)

@unittest.skipUnless(shutil.which('cc') and shutil.which('bwrap'),'cc et bwrap requis')
class CompileOutputTests(unittest.TestCase):
    def test_failed_command_cleans_its_own_output(self):
        def fake(command,cwd,timeout,limited=False,pass_fds=()):
            os.write(pass_fds[0],b'{"child-pid":123}\n{"exit-code":1}\n');return 1,b'',b'bad',False
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'ft_putchar.c').write_text('x')
            runner=ExperimentalRunner(fake)
            args=[shutil.which('cc'),'-Wall','-Wextra','-Werror','-fno-builtin','-c','ft_putchar.c','-o','submission.o']
            self.assertEqual(runner(args,p,5)[0],1)
            self.assertFalse((p/'submission.o').exists())

    def test_exception_cleans_output_but_does_not_delete_replacement(self):
        for replaced in (False,True):
            with self.subTest(replaced=replaced),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);(p/'ft_putchar.c').write_text('x');out=p/'submission.o'
                def fake(command,cwd,timeout,limited=False,pass_fds=()):
                    if replaced:
                        out.unlink();out.write_text('replacement')
                    raise OSError('runner failed')
                runner=ExperimentalRunner(fake)
                args=[shutil.which('cc'),'-Wall','-Wextra','-Werror','-fno-builtin','-c','ft_putchar.c','-o','submission.o']
                with self.assertRaises(OSError):runner(args,p,5)
                if replaced:self.assertEqual(out.read_text(),'replacement')
                else:self.assertFalse(out.exists())

class DisabledProbeCliTests(unittest.TestCase):
    def test_direct_invocation_is_unavailable_and_nonzero(self):
        p=subprocess.run([sys.executable,'-m','moulinette.cgroup_load_probe'],capture_output=True,timeout=5)
        self.assertEqual(p.returncode,2);self.assertEqual(json.loads(p.stdout)['status'],'unavailable')

class InterruptSignalTests(unittest.TestCase):
    def _run_and_terminate(self,script):
        with tempfile.TemporaryDirectory() as root:
            code=Path(root)/'code';code.mkdir();(code/'ft_putchar.c').write_text('void ft_putchar(char c){}')
            env=dict(os.environ,TMPDIR=root,XDG_DATA_HOME=root,ML_TEST_SOURCE=str(code))
            proc=subprocess.Popen([sys.executable,'-c',script],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                ready,_,_=select.select([proc.stderr],[],[],10)
                self.assertTrue(ready,'enfant non prêt');self.assertEqual(proc.stderr.readline(),b'READY\n')
                proc.send_signal(signal.SIGTERM)
                out,err=proc.communicate(timeout=10)
                return proc.returncode,out,err,[p.name for p in Path(root).glob('moulinette-*')]
            finally:
                if proc.poll() is None:proc.kill();proc.wait(timeout=5)
    def test_cli_sigterm_emits_incomplete_json_and_cleans_workdir(self):
        script='''import os,sys,time\nfrom moulinette import checker,cli\ndef slow(*a,**kw):\n print('READY',file=sys.stderr,flush=True);time.sleep(30)\nchecker._run=slow\nraise SystemExit(cli.main(['check',os.environ['ML_TEST_SOURCE'],'--exercise','c00/ex00','--unsafe-local','--no-history','--json']))\n'''
        code,out,err,left=self._run_and_terminate(script)
        self.assertEqual(code,2,err);self.assertEqual(json.loads(out)['result'],'incomplete');self.assertEqual(left,[])
    def test_sigterm_stops_actual_capture_child_and_cleans_workdir(self):
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'code';source.mkdir();(source/'ft_putchar.c').write_text('void ft_putchar(char c){}')
            marker=Path(root)/'child-ready'
            script="""import os,sys
from pathlib import Path
from moulinette import checker,cli
from moulinette.process_capture import run_bounded
child="import os,time;open(os.environ['MARKER'],'w').write(str(os.getpid()));time.sleep(30)"
def slow(*a,**kw): return run_bounded([sys.executable,'-c',child],Path('/'),30,dict(os.environ),lambda:None)
checker._run=slow
raise SystemExit(cli.main(['check',os.environ['ML_TEST_SOURCE'],'--exercise','c00/ex00','--unsafe-local','--no-history','--json']))
"""
            env=dict(os.environ,TMPDIR=root,ML_TEST_SOURCE=str(source),MARKER=str(marker))
            proc=subprocess.Popen([sys.executable,'-c',script],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            pidfd=None
            try:
                deadline=time.monotonic()+8
                contents=''
                while proc.poll() is None and time.monotonic()<deadline:
                    try: contents=marker.read_text()
                    except FileNotFoundError: pass
                    if contents.isdecimal(): break
                    time.sleep(0.02)
                self.assertTrue(contents.isdecimal(),'enfant de capture non démarré')
                pid=int(contents)
                if hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'):
                    try: pidfd=os.pidfd_open(pid)
                    except OSError: pass
                proc.send_signal(signal.SIGTERM)
                out,err=proc.communicate(timeout=10)
                self.assertEqual(proc.returncode,2,err);self.assertEqual(json.loads(out)['result'],'incomplete')
                self.assertEqual(list(Path(root).glob('moulinette-*')),[])
                with self.assertRaises(ProcessLookupError):os.kill(pid,0)
            finally:
                if proc.poll() is None:proc.kill();proc.wait(timeout=5)
                if pidfd is not None:
                    try: signal.pidfd_send_signal(pidfd,signal.SIGKILL)
                    except ProcessLookupError: pass
                    finally: os.close(pidfd)
    def test_interrupt_cleanup_diagnostic_in_json(self):
        exc=KeyboardInterrupt();exc._moulinette_cleanup_error='Arrêt du processus non confirmé.'
        output=io.StringIO()
        with patch('moulinette.cli.check_ex00',side_effect=exc),contextlib.redirect_stdout(output):
            code=cli.main(['check','/tmp/fake','--exercise','c00/ex00','--unsafe-local','--no-history','--json'])
        self.assertEqual(code,2);self.assertIn('non confirmé',json.loads(output.getvalue())['checks'][0]['message'])
    def test_worker_sigterm_unwinds_workdir(self):
        script='''import os,sys,time\nfrom unittest.mock import patch\nfrom moulinette import checker,cgroup_worker as w\ndef slow(*a,**kw):\n print('READY',file=sys.stderr,flush=True);time.sleep(30)\nclass Sock:\n def __enter__(self): return self\n def __exit__(self,*a): pass\n def settimeout(self,*a):pass\n def connect(self,*a):pass\nstate={'pids_max':32,'memory_max':536870912,'cpu_quota':100000,'cpu_period':100000}\nrequest={'action':'run','path':os.environ['ML_TEST_SOURCE'],'exercise':'c00/ex00'}\nchecker._run=slow\nwith patch.object(w.socket,'socket',return_value=Sock()),patch.object(w,'verify_current_scope',return_value=state),patch.object(w,'send_object'),patch.object(w,'receive_object',return_value=request),patch.object(checker,'ExperimentalRunner',side_effect=lambda fn,exercise: fn):\n raise SystemExit(w.main(['--socket','/tmp/fake','--scope','fake']))\n'''
        code,out,err,left=self._run_and_terminate(script)
        self.assertEqual(code,2,err);self.assertEqual(left,[])

if __name__=='__main__':unittest.main()

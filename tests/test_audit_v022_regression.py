"""Constats vérifiés sur le code v0.22, sans saturation ni OOM."""
import contextlib
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from moulinette import cli
from moulinette.checker import check_ex00
from moulinette.history import read_history,store_attempt
from moulinette.sandbox_runner import ExperimentalRunner
from moulinette.process_capture import run_bounded

GOOD_REPORT={'exercise':'42/c/c00/ex00','subject_version':'8','profile':'42-autodidacte','isolation':'test',
             'checks':[{'name':'Fixture','status':'pass','message':'ok'}],'result':'passed'}

class InterruptPhases(unittest.TestCase):
    def test_interrupt_in_history_returns_incomplete_valid_json(self):
        out=io.StringIO()
        with patch('moulinette.cli.check_ex00',return_value=dict(GOOD_REPORT)), \
             patch('moulinette.cli.store_attempt',side_effect=KeyboardInterrupt()),contextlib.redirect_stdout(out):
            code=cli.main(['check','/tmp/x','--exercise','c00/ex00','--unsafe-local','--json'])
        self.assertEqual(code,2);result=json.loads(out.getvalue());self.assertEqual(result['result'],'incomplete')
        self.assertIn('historique',result['checks'][0]['message'].lower())
    def test_two_sigterms_across_nested_launcher_and_history(self):
        script = """import os,signal
from unittest.mock import patch, MagicMock
from moulinette import cli
from moulinette.cgroup_launcher import _termination_signals
def launch(*args):
 with _termination_signals():
  try: os.kill(os.getpid(),signal.SIGTERM)
  except KeyboardInterrupt: return None,'Correction interrompue.'
def store(*args): os.kill(os.getpid(),signal.SIGTERM)
with patch.object(cli,'launch_cgroup',side_effect=launch),patch.object(cli,'store_attempt',side_effect=store):
 raise SystemExit(cli.main(['check','/tmp/test','--exercise','c00/ex00','--experimental-cgroup-sandbox','--json']))
"""
        proc=subprocess.run([sys.executable,'-c',script],capture_output=True,timeout=10)
        self.assertEqual(proc.returncode,2,proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['result'],'incomplete')
        self.assertIn('historique',json.loads(proc.stdout)['checks'][0]['message'].lower())
    def test_dashboard_interrupt_returns_clean_nonzero(self):
        err=io.StringIO()
        with patch('moulinette.cli.write_dashboard',side_effect=KeyboardInterrupt()),contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(['dashboard','--no-open']),2)
        self.assertIn('interromp',err.getvalue().lower());self.assertNotIn('Traceback',err.getvalue())

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc'),'bwrap et cc requis')
class DiagnosticCleanup(unittest.TestCase):
    def test_annotated_oserror_with_replaced_output_reaches_report(self):
        def runner(cmd,cwd,timeout,limited=False,pass_fds=()):
            output=Path(cwd)/'submission.o';output.unlink();output.write_text('remplacement')
            err=OSError('erreur initiale');err._moulinette_cleanup_error='arrêt du groupe non confirmé'
            raise err
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'src';src.mkdir();(src/'ft_putchar.c').write_text('void ft_putchar(char c){ (void)c; }')
            with patch('moulinette.checker._run',runner):report=check_ex00(src,sandbox=True)
        self.assertEqual(report['result'],'incomplete')
        message=' '.join(x['message'] for x in report['checks'])
        self.assertIn('erreur initiale',message);self.assertIn('arrêt du groupe non confirmé',message)
        self.assertIn('Nettoyage de la sortie de compilation non confirmé',message)
    def test_interrupt_preserves_both_cleanup_diagnostics(self):
        def runner(cmd,cwd,timeout,limited=False,pass_fds=()):
            output=Path(cwd)/'submission.o';output.unlink();output.write_text('remplacement')
            exc=KeyboardInterrupt();exc._moulinette_cleanup_error='arrêt du groupe non confirmé';raise exc
        with tempfile.TemporaryDirectory() as t:
            work=Path(t);(work/'ft_putchar.c').write_text('x')
            args=[shutil.which('cc'),'-Wall','-Wextra','-Werror','-fno-builtin','-c','ft_putchar.c','-o','submission.o']
            with self.assertRaises(KeyboardInterrupt) as ctx:ExperimentalRunner(runner)(args,work,10)
        self.assertIn('arrêt du groupe non confirmé',ctx.exception._moulinette_cleanup_error)
        self.assertIn('Nettoyage de la sortie de compilation non confirmé',ctx.exception._moulinette_cleanup_error)

class ProcessDiagnostics(unittest.TestCase):
    def test_group_kill_failure_and_wait_timeout_are_both_retained(self):
        r1,w1=os.pipe();r2,w2=os.pipe();os.close(w1);os.close(w2)
        proc=MagicMock(pid=654321,stdout=os.fdopen(r1,'rb',buffering=0),stderr=os.fdopen(r2,'rb',buffering=0))
        proc.wait.side_effect=subprocess.TimeoutExpired('test',0.5)
        with patch('moulinette.process_capture.subprocess.Popen',return_value=proc), \
             patch('moulinette.process_capture.os.waitid',side_effect=KeyboardInterrupt), \
             patch('moulinette.process_capture.os.killpg',side_effect=PermissionError('test')):
            with self.assertRaises(KeyboardInterrupt) as caught:run_bounded(['fixture'],Path('/tmp'),1,{},lambda:None)
        message=caught.exception._moulinette_cleanup_error
        self.assertIn('Arrêt du groupe impossible',message);self.assertIn('Arrêt du processus non confirmé',message)

class Provenance(unittest.TestCase):
    def test_direct_history_github_surrogates_are_escaped(self):
        report=dict(GOOD_REPORT,source={'kind':'github','url':'https://github.com/a/b','commit':'1'*40,'subdir':'bad\udcff'})
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{'XDG_DATA_HOME':t}):
            store_attempt(report,'/fake');history=read_history()
        label=history['recent'][0]['source_label'];self.assertIn('bad\\udcff',label);label.encode('utf-8')
    def test_local_directory_non_utf8_is_rendered_as_valid_utf8(self):
        with tempfile.TemporaryDirectory() as root:
            source=Path(os.fsdecode(os.fsencode(root)+b'/ex00-\xff'));source.mkdir()
            (source/'unexpected').write_text('x')
            out=io.StringIO()
            with patch.dict(os.environ,{'XDG_DATA_HOME':root}),contextlib.redirect_stdout(out):
                rc=cli.main(['check',str(source),'--exercise','c00/ex00','--unsafe-local','--json'])
                self.assertEqual(read_history()['count'],1)
            self.assertEqual(rc,1);out.getvalue().encode('utf-8','strict');self.assertEqual(json.loads(out.getvalue())['result'],'failed')

if __name__=='__main__': unittest.main()

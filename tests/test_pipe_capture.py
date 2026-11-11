"""Témoins bornés de capture par tubes ; pas de code étudiant non fiable."""
import os
import shutil
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from moulinette.checker import _run, MAX_CAPTURE

class PipeCaptureTests(unittest.TestCase):
    def run_python(self, script, timeout=3):
        return _run([sys.executable,'-c',script],Path('/tmp'),timeout)

    def test_stdout_is_nonseekable_and_write_only(self):
        script = '''import errno,os\ntry: os.lseek(1,0,os.SEEK_SET)\nexcept OSError as e: seek=e.errno\nelse: seek=0\ntry: os.read(1,1)\nexcept OSError as e: read=e.errno\nelse: read=0\nos.write(1, str(seek).encode()+b" "+str(read).encode())\n'''
        import errno
        code,out,err,timeout=self.run_python(script)
        self.assertEqual((code,out,err,timeout),(0,f'{errno.ESPIPE} {errno.EBADF}'.encode(),b'',False))

    def test_drains_both_streams_without_deadlock_and_caps_capture(self):
        script='import os\nfor _ in range(20):\n os.write(1,b"a"*8192); os.write(2,b"b"*8192)\n'
        code,out,err,timeout=self.run_python(script)
        self.assertEqual(code,0); self.assertFalse(timeout)
        self.assertEqual(out,b'a'*MAX_CAPTURE); self.assertEqual(err,b'b'*MAX_CAPTURE)

    def test_closed_pipes_do_not_cancel_timeout(self):
        code,out,err,timeout=self.run_python('import os,time\nos.close(1); os.close(2); time.sleep(2)\n',timeout=0.15)
        self.assertTrue(timeout); self.assertEqual(out,b''); self.assertEqual(err,b'')
        self.assertLess(code,0)

    @unittest.skipUnless(hasattr(os,'fork'), 'fork requis')
    def test_inherited_open_pipes_do_not_wait_indefinitely_or_validate(self):
        # Un seul descendant témoin, qui s'arrête seul après une seconde.
        script='''import os,time\npid=os.fork()\nif pid==0:\n os.setsid(); time.sleep(1); os._exit(0)\nos.write(1,(str(pid)+"\\n").encode())\nos._exit(0)\n'''
        # Le témoin doit être auto-borné car le PID ne sera pas renvoyé si la capture est indéterminée.
        started=time.monotonic()
        with self.assertRaises(OSError): self.run_python(script,timeout=3)
        self.assertLess(time.monotonic()-started,1.0)

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap et outils C requis')
class SandboxPipeTests(unittest.TestCase):
    def test_real_bwrap_process_receives_pipe_not_host_regular_file(self):
        from moulinette.sandbox_doctor import diagnose
        from moulinette.sandbox_runner import ExperimentalRunner
        relevant=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not relevant or any(x['status']!='pass' for x in relevant): raise unittest.SkipTest('Bubblewrap indisponible')
        cc=shutil.which('cc')
        harness='''#include <sys/stat.h>\n#include <unistd.h>\nint main(void) { struct stat st; if (fstat(1,&st) != 0) return 1; if (!S_ISFIFO(st.st_mode)) return 2; return write(1,"P",1) == 1 ? 0 : 3; }\n'''
        with tempfile.TemporaryDirectory() as t:
            p=Path(t); (p/'ft_putchar.c').write_text('void ft_putchar(char c) { (void)c; }\n'); (p/'harness.c').write_text(harness)
            runner=ExperimentalRunner(_run)
            cc_result=runner([cc,'-Wall','-Wextra','-Werror','-fno-builtin','-c','ft_putchar.c','-o','submission.o'],p,10)
            self.assertEqual(cc_result[0],0,cc_result)
            link_result=runner([cc,'-Wall','-Wextra','-Werror','-std=c11','harness.c','submission.o','-o','test-ex00'],p,10)
            self.assertEqual(link_result[0],0,link_result)
            code,out,err,timeout=runner([str(p/'test-ex00'),'1'],p,3,limited=True)
            self.assertEqual((code,out,timeout),(0,b'P',False),err)


    def test_real_bwrap_test_has_no_open_extra_fds_3_to_1023(self):
        from moulinette.sandbox_doctor import diagnose
        from moulinette.sandbox_runner import ExperimentalRunner
        relevant=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not relevant or any(x['status']!='pass' for x in relevant): raise unittest.SkipTest('Bubblewrap indisponible')
        cc=shutil.which('cc')
        harness = ('#include <sys/stat.h>\n#include <unistd.h>\n'
                   'int main(void) { struct stat st; int i; for (i=3;i<1024;i++) '
                   'if (fstat(i,&st)==0) return 8; return 0; }\n')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'ft_putchar.c').write_text('void ft_putchar(char c) { (void)c; }\n');(p/'harness.c').write_text(harness)
            runner=ExperimentalRunner(_run)
            a=runner([cc,'-Wall','-Wextra','-Werror','-fno-builtin','-c','ft_putchar.c','-o','submission.o'],p,10)
            self.assertEqual(a[0],0,a)
            b=runner([cc,'-Wall','-Wextra','-Werror','-std=c11','harness.c','submission.o','-o','test-ex00'],p,10)
            self.assertEqual(b[0],0,b)
            code,out,err,timeout=runner([str(p/'test-ex00'),'1'],p,3,limited=True)
            self.assertEqual((code,out,timeout),(0,b'',False),err)

class CaptureRobustnessTests(unittest.TestCase):
    def test_wait_after_kill_has_a_deadline_even_if_child_does_not_exit(self):
        from unittest.mock import MagicMock, patch
        from moulinette.process_capture import run_bounded
        import subprocess
        r1,w1=os.pipe();r2,w2=os.pipe();os.close(w1);os.close(w2)
        fake=MagicMock(pid=654321,stdout=os.fdopen(r1,'rb',buffering=0),stderr=os.fdopen(r2,'rb',buffering=0))
        fake.wait.side_effect=subprocess.TimeoutExpired('fixture',0.5)
        with patch('moulinette.process_capture.subprocess.Popen',return_value=fake), \
             patch('moulinette.process_capture.os.waitid',return_value=None), \
             patch('moulinette.process_capture.os.killpg') as kill:
            start=time.monotonic()
            with self.assertRaisesRegex(OSError,'non confirmé'):
                run_bounded(['fixture'],Path('/tmp'),0.02,{},lambda: None)
            self.assertLess(time.monotonic()-start,0.5)
        kill.assert_called_once_with(654321,signal.SIGKILL)
        fake.wait.assert_called_once_with(timeout=0.5)

    def test_reaped_child_never_signals_a_potentially_reused_pid(self):
        from unittest.mock import MagicMock, patch
        from moulinette.process_capture import run_bounded
        r1,w1=os.pipe();r2,w2=os.pipe();os.close(w1);os.close(w2)
        fake=MagicMock(pid=654321,stdout=os.fdopen(r1,'rb',buffering=0),stderr=os.fdopen(r2,'rb',buffering=0))
        with patch('moulinette.process_capture.subprocess.Popen',return_value=fake), \
             patch('moulinette.process_capture.os.waitid',side_effect=ChildProcessError), \
             patch('moulinette.process_capture.os.killpg') as kill:
            with self.assertRaisesRegex(OSError,'état|État'):
                run_bounded(['fixture'],Path('/tmp'),1,{},lambda: None)
        kill.assert_not_called()

    def test_cleanup_error_is_incomplete_not_failed_or_passed(self):
        from unittest.mock import patch
        from moulinette.checker import check_ex00
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'ft_putchar.c').write_text('void ft_putchar(char c) { (void)c; }\n')
            with patch('moulinette.checker.run_bounded',side_effect=OSError('nettoyage non confirmé')):
                report=check_ex00(Path(tmp))
        self.assertEqual(report['result'],'incomplete')
        self.assertTrue(any(c['status']=='unavailable' and 'nettoyage non confirmé' in c['message'] for c in report['checks']))

    def test_both_streams_bounded_while_process_continues_producing(self):
        script='import os,time\nwhile True:\n os.write(1,b"a"*8192); os.write(2,b"b"*8192)\n'
        started=time.monotonic()
        code,out,err,timeout=_run([sys.executable,'-c',script],Path('/tmp'),0.2)
        self.assertTrue(timeout);self.assertLess(time.monotonic()-started,1.5)
        self.assertEqual(len(out),MAX_CAPTURE);self.assertEqual(len(err),MAX_CAPTURE)

class ResourceWitnessTests(unittest.TestCase):
    def test_memory_rlimit_witness_in_a_trusted_child(self):
        script = ("import resource\n"
                  "soft,hard=resource.getrlimit(resource.RLIMIT_AS)\n"
                  "assert soft==256*1024*1024 and hard==soft\n"
                  "try: x=bytearray(300*1024*1024)\n"
                  "except MemoryError: print('blocked')\n"
                  "else: print('unexpected')\n")
        code,out,err,timeout=_run([sys.executable,'-c',script],Path('/tmp'),3,limited=True)
        self.assertEqual((code,out,err,timeout),(0,b'blocked\n',b'',False))

    def test_cpu_rlimit_witness_in_a_trusted_child(self):
        script='import resource\na,b=resource.getrlimit(resource.RLIMIT_CPU)\nassert (a,b)==(2,3)\nwhile True: pass\n'
        started=time.monotonic()
        code,out,err,timeout=_run([sys.executable,'-c',script],Path('/tmp'),8,limited=True)
        self.assertFalse(timeout)
        self.assertIn(code,(-signal.SIGXCPU,-signal.SIGKILL))
        self.assertLess(time.monotonic()-started,8.8)

    @unittest.skipUnless(hasattr(os,'fork'), 'fork requis')
    def test_descendant_in_same_group_is_terminated_after_parent_exits(self):
        script = ("import os,time\n"
                  "p=os.fork()\n"
                  "if p==0: time.sleep(1.5); os._exit(0)\n"
                  "os.write(1,(str(p)+'\\n').encode()); os._exit(0)\n")
        code,out,err,timeout=_run([sys.executable,'-c',script],Path('/tmp'),3)
        self.assertEqual((code,err,timeout),(0,b'',False))
        pid=int(out.strip())
        try:
            status=Path('/proc')/str(pid)/'stat'
            if status.exists():
                # Un zombie ne s'exécute plus ; le noyau le récolte séparément.
                self.assertEqual(status.read_text().split(') ',1)[1][0],'Z')
        except (FileNotFoundError, ProcessLookupError):
            # Le processus peut disparaître pendant la lecture.
            pass

    def test_proc_disappears_during_read_without_false_failure(self):
        from unittest.mock import patch
        with patch('test_pipe_capture._run', return_value=(0, b'12345\n', b'', False)), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'read_text', side_effect=ProcessLookupError('processus disparu')):
            self.test_descendant_in_same_group_is_terminated_after_parent_exits()

    def test_proc_still_running_is_not_accepted_as_stopped(self):
        from unittest.mock import patch
        with patch('test_pipe_capture._run', return_value=(0, b'12345\n', b'', False)), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'read_text', return_value='12345 (fixture) S 1 1'):
            with self.assertRaises(AssertionError):
                self.test_descendant_in_same_group_is_terminated_after_parent_exits()

if __name__=='__main__': unittest.main()

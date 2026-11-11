import contextlib
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from moulinette import cli, sandbox_selftest

class SelftestTests(unittest.TestCase):
    def test_absent_bwrap_is_incomplete(self):
        with patch('moulinette.sandbox_selftest.shutil.which', return_value=None):
            report = sandbox_selftest.selftest()
        self.assertEqual(report['result'], 'incomplete')
        self.assertEqual(report['checks'][0]['status'], 'unavailable')

    def test_bwrap_error_is_unavailable_and_does_not_execute_probe(self):
        calls = []
        def fail(command):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, '', 'bwrap: permission denied')
        with patch('moulinette.sandbox_selftest.shutil.which', return_value='/usr/bin/bwrap'), \
             patch('moulinette.sandbox_selftest._run', side_effect=fail):
            report = sandbox_selftest.selftest()
        self.assertEqual(len(calls), 1)
        self.assertEqual(report['result'], 'incomplete')
        self.assertIn('permission denied', report['checks'][0]['message'])

    def test_good_probes_are_still_incomplete(self):
        calls = []
        def fake_run(command):
            calls.append(command)
            if 'probe.c' in command:
                work = Path(command[command.index('--bind') + 1])
                (work / 'probe').write_text('dummy')
                return subprocess.CompletedProcess(command, 0, '', '')
            if 'probe-include.c' in command:
                return subprocess.CompletedProcess(command, 1, '', 'No such file or directory')
            return subprocess.CompletedProcess(command, 0, '1 1 1 1\n', '')
        with patch('moulinette.sandbox_selftest.shutil.which', return_value='/usr/bin/bwrap'), \
             patch('moulinette.sandbox_selftest._run', side_effect=fake_run):
            report = sandbox_selftest.selftest()
        self.assertEqual(len(calls), 3)
        self.assertEqual(report['result'], 'incomplete')
        self.assertTrue(any(c['name'] == 'Limites non testées' and c['status'] == 'unavailable' for c in report['checks']))
        self.assertIn('--bind', calls[0])
        self.assertIn('--ro-bind', calls[2])

    def test_cli_never_evaluates_student_code(self):
        fake = {'checks': [], 'result': 'incomplete'}
        with patch('moulinette.cli.selftest', return_value=fake), \
             patch('moulinette.cli.check_ex00', side_effect=AssertionError('correcteur appelé')), \
             contextlib.redirect_stdout(io.StringIO()):
            status = cli.main(['sandbox', 'selftest'])
        self.assertEqual(status, 2)

if __name__ == '__main__':
    unittest.main()

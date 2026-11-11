import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch
from moulinette import cli, sandbox_doctor

class DoctorTests(unittest.TestCase):
    def test_missing_bwrap_reports_unavailable_not_secure(self):
        with patch('moulinette.sandbox_doctor.shutil.which', return_value=None):
            report = sandbox_doctor.diagnose()
        self.assertEqual(report['result'], 'incomplete')
        self.assertEqual(report['checks'][0]['status'], 'unavailable')

    def test_failed_bwrap_is_not_reported_as_success(self):
        fake = [subprocess.CompletedProcess(['bwrap'], 0, 'bubblewrap 1.0\n', ''),
                subprocess.CompletedProcess(['bwrap'], 1, '', 'permission denied')]
        with patch('moulinette.sandbox_doctor.shutil.which', return_value='/usr/bin/bwrap'), \
             patch('moulinette.sandbox_doctor.subprocess.run', side_effect=fake):
            report = sandbox_doctor.diagnose()
        self.assertEqual(report['result'], 'incomplete')
        self.assertTrue(any(c['status'] == 'unavailable' and 'permission denied' in c['message'] for c in report['checks']))

    def test_json_cli_returns_incomplete_and_never_runs_checker(self):
        fake = {'checks': [{'name': 'Bubblewrap', 'status': 'pass', 'message': 'test'}], 'result': 'incomplete', 'purpose': 'diagnostic'}
        out = io.StringIO()
        with patch('moulinette.cli.diagnose', return_value=fake), \
             patch('moulinette.cli.check_ex00', side_effect=AssertionError('correcteur appelé')), \
             contextlib.redirect_stdout(out):
            status = cli.main(['sandbox', 'doctor', '--json'])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(out.getvalue())['result'], 'incomplete')

    def test_json_cli_returns_failure_for_failed_check(self):
        fake = {'checks': [{'name': 'x', 'status': 'fail', 'message': 'test'}], 'result': 'incomplete', 'purpose': 'diagnostic'}
        with patch('moulinette.cli.diagnose', return_value=fake), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['sandbox', 'doctor']), 1)

if __name__ == '__main__':
    unittest.main()

class DoctorEnvironmentTests(unittest.TestCase):
    def test_doctor_does_not_forward_host_environment(self):
        fake = [subprocess.CompletedProcess(['bwrap'], 0, 'bubblewrap 1.0\n', ''),
                subprocess.CompletedProcess(['bwrap'], 1, '', 'permission denied')]
        with patch.dict('os.environ', {'HOST_SECRET_TOKEN': 'do-not-copy'}), \
             patch('moulinette.sandbox_doctor.shutil.which', return_value='/usr/bin/bwrap'), \
             patch('moulinette.sandbox_doctor.subprocess.run', side_effect=fake) as run:
            sandbox_doctor.diagnose()
        self.assertNotIn('HOST_SECRET_TOKEN', run.call_args_list[1].kwargs['env'])
        self.assertIn('MOULINETTE_DOCTOR_CANARY', run.call_args_list[1].kwargs['env'])

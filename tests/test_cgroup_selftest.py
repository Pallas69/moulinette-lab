import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch
from moulinette import cli, cgroup_selftest

GOOD = {'status': 'observed', 'pids_max': '8', 'memory_max': str(128*1024*1024),
        'cpu_max': '100000 100000', 'initial_tasks': 2, 'children_created': 6,
        'children_reaped': 6, 'tasks_at_rejection': 8, 'pids_events_delta': 1, 'rejected': True}

class CgroupSelftestUnitTests(unittest.TestCase):
    def run_fake(self, output, code=0, stderr=''):
        with patch('moulinette.cgroup_selftest.shutil.which', return_value='/usr/bin/systemd-run'), \
             patch('moulinette.cgroup_selftest.subprocess.run', return_value=subprocess.CompletedProcess([], code, output, stderr)) as run:
            report = cgroup_selftest.cgroup_selftest()
        return report, run

    def test_missing_systemd_is_incomplete_without_fallback(self):
        with patch('moulinette.cgroup_selftest.shutil.which', return_value=None), \
             patch('moulinette.cgroup_selftest.subprocess.run', side_effect=AssertionError('ne doit pas lancer de processus')):
            report = cgroup_selftest.cgroup_selftest()
        self.assertEqual(report['result'], 'incomplete')
        self.assertEqual(report['checks'][0]['status'], 'unavailable')

    def test_verified_witness_still_incomplete_and_command_bounded(self):
        report, run = self.run_fake(json.dumps(GOOD))
        self.assertEqual(report['result'], 'incomplete')
        self.assertEqual([x['status'] for x in report['checks']], ['pass', 'pass', 'pass', 'unavailable'])
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:4], ['/usr/bin/systemd-run', '--user', '--scope', '--quiet'])
        self.assertIn('TasksMax=8', cmd)
        self.assertIn('MemoryMax=128M', cmd)
        self.assertIn('CPUQuota=100%', cmd)
        self.assertNotIn('sudo', cmd)
        self.assertEqual(run.call_args.kwargs['timeout'], 10)
        self.assertNotIn('LD_PRELOAD', run.call_args.kwargs['env'])

    def test_bad_status_and_inconsistent_results_are_unavailable(self):
        bad = [dict(GOOD, cpu_max='max 100000'), dict(GOOD, pids_max='max'),
               dict(GOOD, children_reaped=0), dict(GOOD, pids_events_delta=0),
               dict(GOOD, rejected=False), dict(GOOD, initial_tasks=3)]
        for data in bad:
            with self.subTest(data=data):
                report, _ = self.run_fake(json.dumps(data))
                self.assertEqual(report['result'], 'incomplete')
                self.assertFalse(any(x['status'] == 'pass' for x in report['checks']))

    def test_parse_errors_and_systemd_failure_do_not_fallback(self):
        for output, code, stderr in [('not json', 0, ''), ('{}', 0, ''), ('', 1, 'bus unavailable'), ('x'*8193, 0, '')]:
            with self.subTest(code=code, output=output[:20]):
                report, run = self.run_fake(output, code, stderr)
                self.assertEqual(report['result'], 'incomplete')
                self.assertEqual(run.call_count, 1)
                self.assertEqual(report['checks'][0]['status'], 'unavailable')

    def test_timeout_is_unavailable(self):
        with patch('moulinette.cgroup_selftest.shutil.which', return_value='/usr/bin/systemd-run'), \
             patch('moulinette.cgroup_selftest.subprocess.run', side_effect=subprocess.TimeoutExpired('systemd-run', 10)):
            report = cgroup_selftest.cgroup_selftest()
        self.assertEqual(report['result'], 'incomplete')
        self.assertEqual(report['checks'][0]['status'], 'unavailable')

    def test_cli_does_not_call_checker(self):
        with patch('moulinette.cli.cgroup_selftest', return_value={'checks': [], 'result': 'incomplete'}), \
             patch('moulinette.cli.check_ex00', side_effect=AssertionError('aucune correction')), \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(['sandbox', 'cgroup-selftest'])
        self.assertEqual(code, 2)


class ProbeLogicTests(unittest.TestCase):
    def test_probe_observes_pid_cap_and_reaps_all_simulated_children(self):
        import errno
        import os
        from pathlib import Path
        events = iter(['max 0\n', 'max 1\n'])
        current = iter(['2\n', '8\n'])
        def read_text(path, *args, **kwargs):
            if str(path) == '/proc/self/cgroup': return '0::/fake\n'
            name = path.name
            if name == 'cgroup.procs': return str(os.getpid()) + '\n'
            if name == 'pids.max': return '8\n'
            if name == 'memory.max': return str(128*1024*1024) + '\n'
            if name == 'cpu.max': return '100000 100000\n'
            if name == 'pids.current': return next(current)
            if name == 'pids.events': return next(events)
            raise FileNotFoundError(str(path))
        forks = iter([6001, 6002, 6003, 6004, 6005, 6006])
        def fork():
            try: return next(forks)
            except StopIteration: raise OSError(errno.EAGAIN, 'limited')
        out = io.StringIO()
        with patch.object(Path, 'read_text', read_text), patch('os.pipe', return_value=(61, 62)), \
             patch('os.fork', side_effect=fork), patch('os.close') as close, \
             patch('os.waitpid', side_effect=lambda pid, flags: (pid, 0)) as wait, \
             patch('signal.alarm'), contextlib.redirect_stdout(out):
            exec(cgroup_selftest.PROBE, {})
        data = json.loads(out.getvalue())
        self.assertEqual(data['status'], 'observed')
        self.assertEqual(data['children_created'], 6)
        self.assertEqual(data['children_reaped'], 6)
        self.assertEqual(wait.call_count, 6)
        self.assertEqual(close.call_count, 2)

    def test_probe_never_forks_when_requested_limit_missing(self):
        import os
        from pathlib import Path
        def read_text(path, *args, **kwargs):
            if str(path) == '/proc/self/cgroup': return '0::/fake\n'
            return {'cgroup.procs': str(os.getpid()), 'pids.max': 'max', 'memory.max': 'max',
                    'cpu.max': 'max 100000', 'pids.current': '2', 'pids.events': 'max 0'}[path.name]
        out = io.StringIO()
        with patch.object(Path, 'read_text', read_text), patch('os.fork', side_effect=AssertionError('pas de fork')), \
             patch('os.pipe', side_effect=AssertionError('pas de tube')), patch('signal.alarm'), contextlib.redirect_stdout(out):
            exec(cgroup_selftest.PROBE, {})
        self.assertEqual(json.loads(out.getvalue())['status'], 'unavailable')

if __name__ == '__main__':
    unittest.main()

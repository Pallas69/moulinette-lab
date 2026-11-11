import contextlib
import io
import json
import socket
import subprocess
import threading
import unittest
from unittest.mock import patch
from moulinette import cgroup_launcher, cgroup_worker, cli
from support_audit import successful_report
from moulinette.cgroup_gate import CgroupGateUnavailable
from moulinette.scope_protocol import receive_object, send_object

SCOPE = 'moulinette-' + 'a' * 32 + '.scope'
STATE = {'scope': SCOPE, 'group': '/user.slice/' + SCOPE, 'pids_max': 32,
         'memory_max': 536870912, 'cpu_quota': 100000, 'cpu_period': 100000}
REPORT = successful_report('c00/ex00')

class WorkerTests(unittest.TestCase):
    def run_worker(self, gate_results, request=None):
        parent, child = socket.socketpair()
        output = []
        def work():
            with child:
                output.append(cgroup_worker.serve(child, SCOPE))
        with parent, patch('moulinette.cgroup_worker.verify_current_scope', side_effect=gate_results) as gate, \
             patch('moulinette.cgroup_worker.check_ex00', return_value=dict(REPORT)) as checker:
            parent.settimeout(2)
            thread = threading.Thread(target=work); thread.start()
            first = receive_object(parent)
            second = None
            if first.get('phase') == 'ready':
                send_object(parent, request if request is not None else {'action': 'run', 'path': '/trusted', 'exercise': 'c00/ex00'})
                second = receive_object(parent)
            thread.join(2)
            self.assertFalse(thread.is_alive())
        return first, second, output, gate.call_count, checker.call_count

    def test_gate_failure_never_runs_checker(self):
        first, _, code, _, calls = self.run_worker([CgroupGateUnavailable('non contrôlé')])
        self.assertEqual(first['phase'], 'unavailable')
        self.assertEqual(code, [2]); self.assertEqual(calls, 0)

    def test_worker_runs_only_after_two_validations_and_go(self):
        first, second, code, gate_calls, calls = self.run_worker([STATE, STATE])
        self.assertEqual(first['phase'], 'ready')
        self.assertEqual(second['phase'], 'result')
        self.assertEqual(second['report']['cgroup_limits']['pids_max'], 32)
        self.assertEqual(code, [0]); self.assertEqual(gate_calls, 2); self.assertEqual(calls, 1)

    def test_later_gate_failure_never_runs_checker(self):
        first, second, code, _, calls = self.run_worker([STATE, CgroupGateUnavailable('limite changée')])
        self.assertEqual(first['phase'], 'ready'); self.assertEqual(second['phase'], 'unavailable')
        self.assertEqual(code, [2]); self.assertEqual(calls, 0)

    def test_invalid_request_never_runs_checker(self):
        first, second, code, _, calls = self.run_worker([STATE], {'action': 'run', 'path': 'https://bad', 'exercise': 'c00/ex00'})
        self.assertEqual(second['phase'], 'unavailable'); self.assertEqual(code, [2]); self.assertEqual(calls, 0)

class LauncherTests(unittest.TestCase):
    def test_absent_systemd_has_no_fallback(self):
        with patch('moulinette.cgroup_launcher.shutil.which', return_value=None), \
             patch('moulinette.cgroup_launcher.subprocess.Popen', side_effect=AssertionError('pas de lancement')):
            report, error = cgroup_launcher.launch('/trusted', 'c00/ex00')
        self.assertIsNone(report); self.assertIn('aucune correction lancée', error)

    def test_cli_fails_closed_when_launcher_unavailable(self):
        with patch('moulinette.cli.launch_cgroup', return_value=(None, 'scope indisponible')), \
             patch('moulinette.cli.check_ex00', side_effect=AssertionError('pas de fallback')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(['check', '/trusted', '--exercise', 'c00/ex00', '--experimental-cgroup-sandbox', '--json','--no-history'])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue())['result'], 'incomplete')

    def test_simulated_success_waits_for_scope_and_cleanup(self):
        import re
        calls = []
        class FakeProcess:
            def __init__(self, cmd, **kwargs):
                calls.append(cmd)
                scope = next(x.split('=',1)[1] for x in cmd if x.startswith('--unit='))
                sockpath = cmd[cmd.index('--socket')+1]
                def simulate_worker():
                    state = dict(STATE, scope=scope, group='/user.slice/'+scope)
                    def gate(*args, **kwargs): return state
                    with patch('moulinette.cgroup_worker.verify_current_scope', side_effect=gate), \
                         patch('moulinette.cgroup_worker.check_ex00', return_value=dict(REPORT)):
                        self.code = cgroup_worker.main(['--socket', sockpath, '--scope', scope])
                self.code = None
                self.thread = threading.Thread(target=simulate_worker); self.thread.start()
                self.pid = 999999
            def poll(self): return self.code
            def wait(self, timeout=None):
                self.thread.join(timeout)
                if self.thread.is_alive(): raise subprocess.TimeoutExpired('fake', timeout)
                return self.code
        def parent_gate(scope, **kwargs): return dict(STATE, scope=scope, group='/user.slice/'+scope)
        with patch('moulinette.cgroup_launcher.shutil.which', side_effect=lambda n: '/usr/bin/'+n), \
             patch('moulinette.cgroup_launcher.subprocess.Popen', FakeProcess), \
             patch('moulinette.cgroup_launcher.verify_current_scope', side_effect=parent_gate), \
             patch('moulinette.cgroup_launcher._events', side_effect=[1, 0]), \
             patch('moulinette.cgroup_launcher._stop') as stop:
            report, error = cgroup_launcher.launch('/trusted', 'c00/ex00')
        self.assertIsNone(error)
        self.assertEqual(report['result'], 'passed')
        self.assertEqual(report['cgroup_limits']['swap_max'], 0)
        self.assertEqual(stop.call_count, 1)
        self.assertIn('MemorySwapMax=0', calls[0]); self.assertIn('TasksMax=32', calls[0])
        self.assertTrue(any(re.fullmatch(r'--unit=moulinette-[a-f0-9]{32}\.scope', x) for x in calls[0]))

    def test_unclean_scope_never_returns_success(self):
        # Même un rapport favorable est rejeté si le groupe reste peuplé.
        class FakeProcess:
            def __init__(self, cmd, **kwargs):
                scope = next(x.split('=',1)[1] for x in cmd if x.startswith('--unit='))
                sockpath = cmd[cmd.index('--socket')+1]
                self.code = None
                def worker():
                    def gate(*a, **kw): return dict(STATE, scope=scope, group='/user.slice/'+scope)
                    with patch('moulinette.cgroup_worker.verify_current_scope', side_effect=gate), \
                         patch('moulinette.cgroup_worker.check_ex00', return_value=dict(REPORT)):
                        self.code = cgroup_worker.main(['--socket', sockpath, '--scope', scope])
                self.thread = threading.Thread(target=worker); self.thread.start()
                self.pid = 999999
            def poll(self): return self.code
            def wait(self, timeout=None):
                self.thread.join(timeout)
                if self.thread.is_alive(): raise subprocess.TimeoutExpired('fake', timeout)
                return self.code
        def gate(scope, **kwargs): return dict(STATE, scope=scope, group='/user.slice/'+scope)
        with patch('moulinette.cgroup_launcher.shutil.which', side_effect=lambda n: '/usr/bin/'+n), \
             patch('moulinette.cgroup_launcher.subprocess.Popen', FakeProcess), \
             patch('moulinette.cgroup_launcher.verify_current_scope', side_effect=gate), \
             patch('moulinette.cgroup_launcher._events', return_value=1), \
             patch('moulinette.cgroup_launcher._stop'), \
             patch('moulinette.cgroup_launcher.os.killpg'):
            report, error = cgroup_launcher.launch('/trusted', 'c00/ex00')
        self.assertIsNone(report); self.assertIn('non confirmé', error)

if __name__ == '__main__':
    unittest.main()

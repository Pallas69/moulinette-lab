import os
import tempfile
import unittest
from pathlib import Path
from moulinette.cgroup_gate import verify_current_scope, CgroupGateUnavailable

SCOPE = 'moulinette-' + 'a' * 32 + '.scope'

class ScopeGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'cg'
        self.base = self.root / 'user.slice' / SCOPE
        self.base.mkdir(parents=True)
        self.proc = Path(self.tmp.name) / 'proc-self-cgroup'
        self.proc.write_text('0::/user.slice/' + SCOPE + '\n')
        (self.base / 'cgroup.procs').write_text(str(os.getpid()) + '\n')
        (self.base / 'pids.max').write_text('32\n')
        (self.base / 'memory.max').write_text('536870912\n')
        (self.base / 'cpu.max').write_text('100000 100000\n')

    def check(self, scope=SCOPE):
        return verify_current_scope(scope, root=self.root, proc_cgroup=self.proc)

    def test_user_observed_values_and_membership_are_accepted(self):
        result = self.check()
        self.assertEqual(result['pids_max'], 32)
        self.assertEqual(result['memory_max'], 536870912)
        self.assertEqual(result['cpu_quota'], result['cpu_period'])

    def test_unlimited_or_too_high_controls_are_rejected(self):
        for name, bad in [('pids.max', 'max'), ('pids.max', '33'), ('pids.max', '0'),
                          ('memory.max', 'max'), ('memory.max', '536870913'),
                          ('cpu.max', 'max 100000'), ('cpu.max', '100001 100000'),
                          ('cpu.max', '100000 0')]:
            with self.subTest(name=name, value=bad):
                original = (self.base / name).read_text()
                (self.base / name).write_text(bad)
                with self.assertRaises(CgroupGateUnavailable): self.check()
                (self.base / name).write_text(original)

    def test_stricter_limits_are_accepted(self):
        (self.base / 'pids.max').write_text('8')
        (self.base / 'memory.max').write_text('134217728')
        (self.base / 'cpu.max').write_text('50000 100000')
        self.assertEqual(self.check()['pids_max'], 8)

    def test_missing_membership_and_files_fail_closed(self):
        (self.base / 'cgroup.procs').write_text('9999999\n')
        with self.assertRaises(CgroupGateUnavailable): self.check()
        (self.base / 'cgroup.procs').write_text(str(os.getpid()))
        (self.base / 'pids.max').unlink()
        with self.assertRaises(CgroupGateUnavailable): self.check()

    def test_unknown_scope_and_ambiguous_or_traversing_group_fail(self):
        with self.assertRaises(CgroupGateUnavailable): self.check('wrong.scope')
        self.proc.write_text('0::/user.slice/' + SCOPE + '\n0::/user.slice/' + SCOPE + '\n')
        with self.assertRaises(CgroupGateUnavailable): self.check()
        self.proc.write_text('0::/../' + SCOPE + '\n')
        with self.assertRaises(CgroupGateUnavailable): self.check()

    def test_symlink_outside_hierarchy_is_refused(self):
        # Remplacer le scope par un lien vers un emplacement externe.
        outside = Path(self.tmp.name) / SCOPE
        outside.mkdir()
        for path in self.base.iterdir(): path.unlink()
        self.base.rmdir()
        self.base.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(CgroupGateUnavailable): self.check()

    def test_required_swap_limit_must_be_zero(self):
        with self.assertRaises(CgroupGateUnavailable):
            verify_current_scope(SCOPE, root=self.root, proc_cgroup=self.proc, swap_max=0)
        (self.base / 'memory.swap.max').write_text('max')
        with self.assertRaises(CgroupGateUnavailable):
            verify_current_scope(SCOPE, root=self.root, proc_cgroup=self.proc, swap_max=0)
        (self.base / 'memory.swap.max').write_text('0')
        self.assertEqual(verify_current_scope(SCOPE, root=self.root, proc_cgroup=self.proc, swap_max=0)['pids_max'], 32)

if __name__ == '__main__':
    unittest.main()

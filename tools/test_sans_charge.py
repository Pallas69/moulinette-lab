"""Suite sans six témoins actifs de limites et de boucles connus.

Cette sélection n'exécute ni les tests de tests_real ni cgroup-selftest. Elle
compile et exécute des exemples de confiance ; elle n'est pas un test à charge
nulle. Si les tests changent, réexaminer la sélection avant toute utilisation.
"""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

EXCLUDED={
    'test_experimental_runner.CompilationMountTests.test_tmpfs_rejects_writes_over_size_limit',
    'test_checker.CheckEx00Tests.test_infinite_loop',
    'test_experimental_runner.AuditFixTests.test_real_student_timeout_is_incomplete_and_identifies_phase',
    'test_pipe_capture.CaptureRobustnessTests.test_both_streams_bounded_while_process_continues_producing',
    'test_pipe_capture.ResourceWitnessTests.test_memory_rlimit_witness_in_a_trusted_child',
    'test_pipe_capture.ResourceWitnessTests.test_cpu_rlimit_witness_in_a_trusted_child',
}

def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flatten(item)
        else:yield item

def main():
    discovered=list(flatten(unittest.defaultTestLoader.discover(str(ROOT/'tests'))))
    found={test.id() for test in discovered}
    if not EXCLUDED <= found:
        print('Sélection invalide : témoins attendus absents : '+', '.join(sorted(EXCLUDED-found)),file=sys.stderr)
        return 2
    print('Témoins de limites exclus :',flush=True)
    for name in sorted(EXCLUDED):print('  '+name,flush=True)
    selected=unittest.TestSuite(test for test in discovered if test.id() not in EXCLUDED)
    result=unittest.TextTestRunner(verbosity=1).run(selected)
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())

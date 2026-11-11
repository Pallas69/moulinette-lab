"""Intégration opt-in : scope systemd utilisateur réel avec exemple de confiance.

À exécuter uniquement sur une machine Ubuntu adaptée et avec l'accord de
l'utilisateur, par `python3 -m unittest discover -s tests_real -v`. Ce test
ne démontre pas la résistance au code hostile et ne sature pas les ressources.
"""
import unittest
from pathlib import Path
from moulinette.cgroup_launcher import launch

ROOT=Path(__file__).resolve().parent.parent

class RealUserScopeTest(unittest.TestCase):
    def test_trusted_example_with_real_scope_and_bwrap(self):
        report,error=launch(ROOT/'exemples'/'ft_putchar','c00/ex00')
        self.assertIsNone(error, 'Scope réel indisponible ou correction impossible : ' + str(error))
        self.assertEqual(report['result'],'passed',report)
        self.assertEqual(report['exercise'],'42/c/c00/ex00')
        self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in report['checks']))
        self.assertEqual(report['cgroup_limits']['swap_max'],0)

    def test_trusted_c01_ft_ft_with_real_scope_and_bwrap(self):
        report,error=launch(ROOT/'exemples'/'c01'/'ex00','c01/ex00')
        self.assertIsNone(error, 'Scope réel indisponible ou correction impossible : ' + str(error))
        self.assertEqual(report['result'],'passed',report)
        self.assertEqual(report['exercise'],'42/c/c01/ex00')
        self.assertEqual(report['subject_version'],'6')
        self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in report['checks']))

    def test_trusted_c02_print_memory_with_real_scope_and_bwrap(self):
        report,error=launch(ROOT/'exemples'/'c02'/'ex12','c02/ex12')
        self.assertIsNone(error, 'Scope réel indisponible ou correction impossible : ' + str(error))
        self.assertEqual(report['result'],'passed',report)
        self.assertEqual(report['exercise'],'42/c/c02/ex12')
        self.assertEqual(report['subject_version'],'6')
        self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in report['checks']))

    def test_trusted_c12_project_with_real_scope_and_bwrap(self):
        # Exemple du projet connu, sans témoin de charge ni saturation.
        report,error=launch(ROOT/'exemples'/'c12'/'ex08','c12/ex08')
        self.assertIsNone(error, 'Scope réel indisponible ou correction impossible : ' + str(error))
        self.assertEqual(report['result'],'passed',report)
        self.assertEqual(report['exercise'],'42/c/c12/ex08')
        self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in report['checks']))
        limits=report['cgroup_limits']
        self.assertLessEqual(limits['pids_max'],32)
        self.assertLessEqual(limits['memory_max'],512*1024*1024)
        self.assertLessEqual(limits['cpu_quota'],limits['cpu_period'])
        self.assertEqual(limits['swap_max'],0)

if __name__=='__main__': unittest.main()

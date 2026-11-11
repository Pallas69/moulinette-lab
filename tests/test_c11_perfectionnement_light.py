"""Régressions C11 avec variantes de confiance, sans tests de saturation."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES

ROOT = Path(__file__).resolve().parents[1] / 'exemples'
TOOLS = all(shutil.which(name) for name in ('cc', 'nm', 'make', 'bwrap', 'norminette'))

@unittest.skipUnless(TOOLS, 'compilateur, Bubblewrap et Norminette nécessaires')
class C11QualityTests(unittest.TestCase):
    def test_five_reference_exercises_pass(self):
        for ident in ('c11/ex01', 'c11/ex02', 'c11/ex05', 'c11/ex06', 'c11/ex07'):
            with self.subTest(exercise=ident):
                report = check_exercise(ROOT / ident, ident, sandbox=True)
                self.assertEqual(report['result'], 'passed', report)

    def test_defects_missed_by_previous_functional_cases(self):
        mutants = [
            ('c11/ex05', 'do_op.c', 'argc == 4', 'argc >= 4',
             ['trop peu d’arguments', 'trop d’arguments', 'opérateur en mot',
              'opérateur avec caractères supplémentaires', 'conversion du premier opérande'],
             'trop d’arguments'),
            ('c11/ex05', 'do_op.c', 's[0] == ops[i] && s[1] == 0', 's[0] == ops[i]',
             ['trop peu d’arguments', 'trop d’arguments', 'opérateur en mot',
              'opérateur avec caractères supplémentaires', 'conversion du premier opérande'],
             'opérateur avec caractères supplémentaires'),
            ('c11/ex01', 'ft_map.c', 'p = malloc(sizeof(int) * n);',
             'if (n == 1)\n\t\treturn (0);\n\tp = malloc(sizeof(int) * n);',
             ['un élément'], 'un élément'),
        ]
        for ident, filename, old, new, added, detects in mutants:
            with self.subTest(exercise=ident, defect=detects), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)
                shutil.copytree(ROOT / ident, target, dirs_exist_ok=True)
                source = target / filename
                text = source.read_text()
                self.assertIn(old, text)
                source.write_text(text.replace(old, new, 1))
                baseline = copy.deepcopy(EXERCISES[ident])
                if 'project' in baseline:
                    baseline['project']['cases'] = [c for c in baseline['project']['cases'] if c['label'] not in added]
                    baseline['cases'] = [c for c in baseline['cases'] if c[0] not in added]
                else:
                    baseline['cases'] = [c for c in baseline['cases'] if c[0] not in added]
                with patch.dict(EXERCISES, {ident: baseline}):
                    before = check_exercise(target, ident, sandbox=True)
                functional = [c for c in before['checks'] if c['name'].startswith('Test ')]
                self.assertEqual(len(functional), len(baseline['cases']), before)
                self.assertTrue(all(c['status'] == 'pass' for c in functional), before)
                after = check_exercise(target, ident, sandbox=True)
                self.assertTrue(any(c['name'] == 'Test ' + detects and c['status'] == 'fail' for c in after['checks']), after)

    def test_any_accepts_full_traversal_as_well_as_short_circuit(self):
        # Ne pas imposer que ft_any s'arrête dès la première correspondance.
        code = '''int ft_any(char **a, int (*f)(char *))
{
 int i=0, found=0;
 while (a[i]) { if (f(a[i])) found=1; i++; }
 return found;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'ft_any.c').write_text(code)
            report = check_exercise(tmp, 'c11/ex02', sandbox=True)
        functional = [c for c in report['checks'] if c['name'].startswith('Test ')]
        self.assertEqual(len(functional), len(EXERCISES['c11/ex02']['cases']), report)
        self.assertTrue(all(c['status'] == 'pass' for c in functional), report)

if __name__ == '__main__':
    unittest.main()

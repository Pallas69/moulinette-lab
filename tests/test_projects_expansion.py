"""Premiers exercices du moteur multi-fichiers, sans prétention officielle."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.cgroup_launcher import _validate_favorable_checks
from moulinette.exercise_catalog import EXERCISES
ROOT=Path(__file__).resolve().parents[1]
IDS=['c07/ex04',*(f'c08/ex{i:02}' for i in range(6)),'c09/ex00','c09/ex01']

@unittest.skipUnless(all(shutil.which(x) for x in ('cc','nm','bwrap','make','norminette','ar')),'outils requis')
class ProjectExercisesTest(unittest.TestCase):
 def test_nine_examples_with_real_bwrap_and_norm(self):
  for ident in IDS:
   with self.subTest(exercise=ident):
    r=check_exercise(ROOT/'exemples'/ident,ident,sandbox=True)
    self.assertEqual(r['result'],'passed',r)
    _validate_favorable_checks(ident,r['checks'])
 def test_invalid_macro_and_missing_file_fail(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'ft_abs.h').write_text('#define ABS(x) (x)\n')
   r=check_exercise(p,'c08/ex02',sandbox=True)
   self.assertEqual(r['result'],'failed',r)
   self.assertTrue(any(x['name'].startswith('Test ') and x['status']=='fail' for x in r['checks']),r)
  with tempfile.TemporaryDirectory() as t:
   (Path(t)/'ft_convert_base.c').write_text('')
   r=check_exercise(t,'c07/ex04',sandbox=True)
   self.assertEqual(r['result'],'failed',r)
 def test_early_wrong_or_forbidden_objects(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   (p/'ft_convert_base.c').write_text('#include <stdio.h>\nchar *ft_convert_base(char*a,char*b,char*c){(void)b;(void)c;puts(a);return 0;}\n')
   (p/'ft_convert_base2.c').write_text('void helper(void) {}\n')
   r=check_exercise(p,'c07/ex04',sandbox=True)
   self.assertEqual(r['result'],'failed',r)
   self.assertTrue(any(x['name']=='Fonctions externes' and x['status']=='fail' for x in r['checks']),r)

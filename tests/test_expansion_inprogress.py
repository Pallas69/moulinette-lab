"""Tests des 38 ajouts préliminaires, avec style simulé ; voir aussi test_all_examples pour le style réel."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES
from moulinette import cli

ROOT=Path(__file__).resolve().parents[1]
IDS=[*(f'c03/ex{i:02}' for i in range(6)),*(f'c04/ex{i:02}' for i in range(6)),
     *(f'c05/ex{i:02}' for i in range(9)),*(f'c06/ex{i:02}' for i in range(4)),
     *(f'c07/ex{i:02}' for i in (0,1,2,3,5)),'c09/ex02',*(f'c11/ex{i:02}' for i in (0,1,2,3,4,6,7))]

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'),'compilateur requis')
class ExpansionFunctional(unittest.TestCase):
 def test_examples_functionally(self):
  with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
   for ident in IDS:
    with self.subTest(ex=ident):
     r=check_exercise(ROOT/'exemples'/ident,ident)
     self.assertEqual(r['result'],'passed',r)
 def test_invalid_program_is_rejected(self):
  with tempfile.TemporaryDirectory() as t,patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
   (Path(t)/'ft_print_params.c').write_text('int main(void) { return 0; }\n')
   r=check_exercise(t,'c06/ex01');self.assertEqual(r['result'],'failed',r)
   self.assertTrue(any(c['name'].startswith('Test ') and c['status']=='fail' for c in r['checks']))
 def test_program_json(self):
  out=io.StringIO()
  with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')),contextlib.redirect_stdout(out):
   code=cli.main(['check',str(ROOT/'exemples/c06/ex01'),'--exercise','c06/ex01','--unsafe-local','--no-history','--json'])
  self.assertEqual(code,0);self.assertEqual(json.loads(out.getvalue())['subject_version'],'8')

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'),'bwrap, cc et nm requis')
class ExpansionBubblewrap(unittest.TestCase):
 def test_examples_in_bwrap_and_report_structure(self):
  from moulinette.cgroup_launcher import _validate_favorable_checks
  with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
   for ident in IDS:
    with self.subTest(ex=ident):
     r=check_exercise(ROOT/'exemples'/ident,ident,sandbox=True)
     self.assertEqual(r['result'],'passed',r)
     _validate_favorable_checks(ident,r['checks'])

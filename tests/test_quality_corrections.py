"""Témoins fonctionnels de régression ; programmes de confiance, sans charge."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES
from moulinette.c01_catalog import _condition_harness

ROOT=Path(__file__).resolve().parents[1]/'exemples'

class HarnessIndexTests(unittest.TestCase):
 def test_more_than_ten_cases_are_selected_independently(self):
  import subprocess
  from moulinette.c01_catalog import _spec
  cases=[('cas '+str(i),f'return {i}==10;') for i in range(12)]
  spec=_spec('dummy','int','void',cases)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'h.c').write_text(spec['harness'].replace('MARKER_BYTES','23,42'))
   subprocess.run(['cc','-Wall','-Wextra','-Werror','-std=c11',str(p/'h.c'),'-o',str(p/'h')],check=True,capture_output=True)
   for index in (0,9,10,11):
    r=subprocess.run([str(p/'h'),str(index)],capture_output=True,timeout=2)
    self.assertEqual(r.returncode,73)
    self.assertEqual(r.stdout,(b'OK' if index==10 else b'KO')+b'\x17\x2a')

@unittest.skipUnless(all(shutil.which(x) for x in ('cc','nm','bwrap','norminette','make','ar')),'outils requis')
class MutationTests(unittest.TestCase):
 def test_added_cases_detect_defects_missed_by_previous_cases(self):
  mutations=[
   ('c05/ex06','ft_is_prime.c',None,'int ft_is_prime(int n) { return n==2 || n==3 || n==97 || n==104729; }\n', ['premier 37','premier 49'],'premier 37'),
   ('c11/ex03','ft_count_if.c',None,'int ft_count_if(char **a, int n, int (*f)(char *)) { int k=0; while(n>0) { n--; if(f(a[n])) k++; } return k; }\n', ['ordre et valeurs du callback'],'ordre et valeurs du callback'),
   ('c12/ex06','ft_list_clear.c','f(p->data);','f(0);',['données transmises au callback'],'données transmises au callback'),
   ('c13/ex06','btree_level_count.c','b = btree_level_count(p->right);','b = 0;',['branche droite plus longue'],'branche droite plus longue'),
   ('c10/ex01','io.c','while (n > 0)','if (n > 0)',['cat binaire de 5 Kio'],'cat binaire de 5 Kio'),
  ]
  for ident,filename,old,new,new_labels,expected in mutations:
   with self.subTest(exercise=ident),tempfile.TemporaryDirectory() as t:
    p=Path(t);shutil.copytree(ROOT/ident,p,dirs_exist_ok=True)
    source=p/filename;text=source.read_text()
    if old is None:text=new
    else:
     self.assertIn(old,text);text=text.replace(old,new,1)
    source.write_text(text)
    current=EXERCISES[ident];baseline=copy.deepcopy(current)
    if 'project' in baseline:
     cases=baseline['project']['cases'];baseline['project']['cases']=[c for c in cases if c['label'] not in new_labels]
     expected_count=len(baseline['project']['cases'])
    else:
     cases=baseline['cases'];baseline['cases']=[c for c in cases if c[0] not in new_labels]
     expected_count=len(baseline['cases'])
    with patch.dict(EXERCISES,{ident:baseline}):
     before=check_exercise(p,ident,sandbox=True)
    checks=[c for c in before['checks'] if c['name'].startswith('Test ')]
    self.assertEqual(len(checks),expected_count,before)
    self.assertTrue(all(c['status']=='pass' for c in checks),before)
    after=check_exercise(p,ident,sandbox=True)
    self.assertTrue(any(c['name']=='Test '+expected and c['status']=='fail' for c in after['checks']),after)

if __name__=='__main__':unittest.main()

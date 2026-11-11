"""Indices non bloquants et vérification de version, sans charge ni OOM."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.recursion_hint import recursion_hint
from moulinette.dashboard_insights import explanations
from moulinette.checker import check_exercise
from moulinette.cgroup_launcher import _validate_favorable_checks
from moulinette.exercise_catalog import EXERCISES

ROOT=Path(__file__).resolve().parents[1]

class RecursionHintTests(unittest.TestCase):
 def test_reference_direct_and_helper_cycles_detected(self):
  for ident in ('c05/ex01','c05/ex03','c05/ex04','c05/ex08'):
   with self.subTest(ident=ident):
    data=(ROOT/'exemples'/ident/EXERCISES[ident]['source']).read_bytes()
    text=recursion_hint(ident,data)
    self.assertIn('cycle possible',text);self.assertIn('pas une preuve',text)
    self.assertIn('ne modifie pas la correction',text)

 def test_absent_unreachable_and_comments_are_not_calls(self):
  content='''int helper(int n) { return helper(n); }
int ft_recursive_factorial(int n) { /* ft_recursive_factorial(n); */
 const char *s = "ft_recursive_factorial(n)"; (void)s; return n; }'''
  msg=recursion_hint('c05/ex01',content)
  self.assertIn('Aucun cycle',msg);self.assertIn('pas une preuve',msg)

 def test_mutual_recursion_is_an_indicative_cycle(self):
  code='''int b(int n); int ft_recursive_factorial(int n) { return b(n); }
int b(int n) { return ft_recursive_factorial(n); }'''
  self.assertIn('cycle possible',recursion_hint('c05/ex01',code))

 def test_indeterminate_and_unrelated_sources(self):
  self.assertIn('indéterminée',recursion_hint('c05/ex01',b'\xff'))
  self.assertIn('indéterminée',recursion_hint('c05/ex01','int other(void) {return 0;}'))
  self.assertIn('indéterminée',recursion_hint('c05/ex01','a '*70000))
  self.assertIsNone(recursion_hint('c05/ex00','int irrelevant;'))

 def test_macro_and_conditional_have_no_guarantee(self):
  code='''#define NEXT(x) ft_recursive_factorial(x)\nint ft_recursive_factorial(int x) { return NEXT(x-1); }'''
  msg=recursion_hint('c05/ex01',code)
  self.assertIn('pas une preuve',msg);self.assertIn('macros',msg)

 @unittest.skipUnless(all(shutil.which(x) for x in ('cc','nm','bwrap','norminette')),'outils requis')
 def test_iterative_code_is_not_rejected_by_hint(self):
  src=('int\tft_recursive_factorial(int n)\n{\n\tint\tvalue;\n\n'
       '\tif (n < 0)\n\t\treturn (0);\n\tvalue = 1;\n\twhile (n > 1)\n'
       '\t{\n\t\tvalue *= n;\n\t\tn--;\n\t}\n\treturn (value);\n}\n')
  with tempfile.TemporaryDirectory() as d:
   Path(d,'ft_recursive_factorial.c').write_text(src)
   report=check_exercise(d,'c05/ex01',sandbox=True)
  self.assertEqual(report['result'],'passed',report)
  hints=[c for c in report['checks'] if c['name']=='Récursivité (indicative)']
  self.assertEqual(len(hints),1);self.assertEqual(hints[0]['status'],'info')
  self.assertIn('Aucun cycle',hints[0]['message'])
  _validate_favorable_checks('c05/ex01',report['checks'])

class VersionAndDiagnosticsTests(unittest.TestCase):
 def test_command_version_and_help(self):
  result=subprocess.run([sys.executable,'-m','moulinette','--version'],cwd=ROOT,text=True,capture_output=True,timeout=5)
  self.assertEqual(result.returncode,0);self.assertEqual(result.stdout.strip(),'moulinette 0.32.8.dev0')
  helptext=subprocess.check_output([sys.executable,'-m','moulinette','--help'],cwd=ROOT,text=True,timeout=5)
  self.assertIn('--version',helptext)

 def test_only_recognized_compile_errors_are_explained(self):
  check={'name':'Compilation','status':'fail','message':"In function 'f':\nerror: unused parameter 'n'\nerror: implicit declaration of function 'ft_putchar'\nerror: expected ';' before 'return'"}
  joined=' '.join(explanations('c00/ex01',check))
  self.assertIn('paramètre « n »',joined);self.assertIn('ft_putchar',joined);self.assertIn('point-virgule',joined)
  self.assertEqual(explanations('c00/ex01',dict(check,status='pass')),[])
  plain=' '.join(explanations('c00/ex01',dict(check,message='autre erreur')))
  self.assertNotIn('paramètre « n »',plain);self.assertNotIn('point-virgule',plain)

if __name__=='__main__':unittest.main()

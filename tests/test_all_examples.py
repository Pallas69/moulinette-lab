"""Validation fonctionnelle et style réels des 109 exemples de confiance."""
import shutil
import unittest
from pathlib import Path
from moulinette.checker import check_exercise
from moulinette.cgroup_launcher import _validate_favorable_checks
from moulinette.exercise_catalog import EXERCISES

ROOT=Path(__file__).resolve().parents[1]/'exemples'
C00=['ft_putchar','ft_print_alphabet','ft_print_reverse_alphabet','ft_print_numbers',
     'ft_is_negative','ft_print_comb','ft_print_comb2','ft_putnbr','ft_print_combn']

def example_path(ident):
 if ident.startswith('c00/'):
  return ROOT/C00[int(ident[-2:])]
 return ROOT/ident

@unittest.skipUnless(all(shutil.which(x) for x in ('cc','nm','bwrap','norminette','make','ar')),'outils réels requis')
class FullExamples(unittest.TestCase):
 def test_all_109_examples_with_real_bwrap_and_norminette(self):
  self.assertEqual(len(EXERCISES),109)
  for ident in sorted(EXERCISES):
   with self.subTest(exercise=ident):
    p=example_path(ident)
    self.assertTrue(p.is_dir(),p)
    r=check_exercise(p,ident,sandbox=True)
    self.assertEqual(r['result'],'passed',r)
    _validate_favorable_checks(ident,r['checks'])
    norm=[x for x in r['checks'] if x['name']=='Norminette adaptée']
    # Makefile seul : il n'y a pas de fichier étudiant C/H à passer en Norminette.
    self.assertTrue(norm and norm[0]['status']==('info' if ident=='c09/ex01' else 'pass'),r)

"""Régressions : des fonctions sans effet ou programmes muets sont rejetés."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES

ROOT=Path(__file__).resolve().parents[1]/'exemples'
LIST_ARGS=[('d',),('p','d'),('p',),('p',),('p','d'),('n','s'),('p','f'),('p','n'),
 ('p',),('p','f'),('p','f','r','cmp'),('p','r','cmp'),('p','r','cmp','f'),('p','b'),
 ('p','cmp'),('p',),('p','d','cmp'),('p','q','cmp')]
TREE_ARGS=[('d',),('p','f'),('p','f'),('p','f'),('p','d','cmp'),('p','d','cmp'),('p',),('p','f')]

@unittest.skipUnless(all(shutil.which(x) for x in ('cc','nm','bwrap','norminette','make','ar')),'outils requis')
class WrongImplementationTests(unittest.TestCase):
 def test_all_list_tree_implementations_without_effect_fail_functionally(self):
  for day,arguments in [('c12',LIST_ARGS),('c13',TREE_ARGS)]:
   for i,args in enumerate(arguments):
    ident=f'{day}/ex{i:02}'
    with self.subTest(exercise=ident),tempfile.TemporaryDirectory() as t:
     p=Path(t);shutil.copytree(ROOT/ident,p,dirs_exist_ok=True)
     source=p/EXERCISES[ident]['source']; original=source.read_text()
     name=source.stem
     match=re.search(r'(?m)^(?:void|int|t_list|t_btree)[\t *]+\**'+name+r'\(',original)
     self.assertIsNotNone(match,ident)
     start=match.start();brace=original.index('{',match.end())
     signature=original[start:brace]
     returns_value=not (signature.startswith('void') and '*' not in signature[:signature.index(name)])
     body=''.join('\t(void)'+x+';\n' for x in args)
     if returns_value:body+='\treturn (0);\n'
     # Garder uniquement le header et la signature du symbole à tester.
     header='ft_list.h' if day=='c12' else 'ft_btree.h'
     source.write_text('#include "'+header+'"\n\n'+signature+'{\n'+body+'}\n')
     r=check_exercise(p,ident,sandbox=True)
     self.assertEqual(r['result'],'failed',r)
     self.assertTrue(any(c['name'].startswith('Test ') and c['status']=='fail' for c in r['checks']),r)
 def test_38_preliminary_additions_reject_no_op(self):
  ids=[*(f'c03/ex{i:02}' for i in range(6)),*(f'c04/ex{i:02}' for i in range(6)),
       *(f'c05/ex{i:02}' for i in range(9)),*(f'c06/ex{i:02}' for i in range(4)),
       *(f'c07/ex{i:02}' for i in (0,1,2,3,5)),'c09/ex02',
       *(f'c11/ex{i:02}' for i in (0,1,2,3,4,6,7))]
  self.assertEqual(len(ids),38)
  for ident in ids:
   with self.subTest(exercise=ident),tempfile.TemporaryDirectory() as t:
    p=Path(t);name=EXERCISES[ident]['source'];sample=(ROOT/ident/name).read_text()
    if ident.startswith('c06/'):
     source='int\tmain(void)\n{\n\treturn (0);\n}\n'
    else:
     symbol=Path(name).stem
     match=re.search(r'(?m)^(?:unsigned int|char|int|void)[\t *]+\**'+symbol+r'\(',sample)
     self.assertIsNotNone(match,ident)
     brace=sample.index('{',match.end());signature=sample[match.start():brace]
     parameters=signature[signature.index('(')+1:signature.rfind(')')]
     chunks=[];begin=0;depth=0
     for pos,char in enumerate(parameters):
      if char=='(':depth+=1
      elif char==')':depth-=1
      elif char==',' and depth==0:
       chunks.append(parameters[begin:pos]);begin=pos+1
     chunks.append(parameters[begin:])
     names=[]
     for chunk in chunks:
      if chunk.strip()=='void':continue
      callback=re.search(r'\(\s*\*\s*(\w+)\s*\)',chunk)
      names.append(callback.group(1) if callback else re.search(r'(\w+)\s*$',chunk).group(1))
     returns=not (signature.startswith('void') and '*' not in signature[:signature.index(symbol)])
     body=''.join('\t(void)'+x+';\n' for x in names)
     if returns:body+='\treturn (0);\n'
     source=signature+'{\n'+body+'}\n'
    (p/name).write_text(source)
    r=check_exercise(p,ident,sandbox=True)
    self.assertEqual(r['result'],'failed',r)
    self.assertTrue(any(c['name'].startswith('Test ') and c['status']=='fail' for c in r['checks']),r)
 def test_c10_programs_silent_and_do_op_silent_fail_functionally(self):
  for ident in ['c10/ex00','c10/ex01','c10/ex02','c10/ex03','c11/ex05']:
   with self.subTest(exercise=ident),tempfile.TemporaryDirectory() as t:
    p=Path(t)
    (p/'main.c').write_text('int\tmain(void)\n{\n\treturn (0);\n}\n')
    if ident.startswith('c10'):
     name=EXERCISES[ident]['project']['binary']
     (p/'Makefile').write_text('all: '+name+'\n'+name+': main.o\n\tcc main.o -o '+name+'\nmain.o: main.c\n\tcc -Wall -Wextra -Werror -c main.c -o main.o\n')
    r=check_exercise(p,ident,sandbox=True)
    self.assertEqual(r['result'],'failed',r)
    self.assertTrue(any(c['name'].startswith('Test ') and c['status']=='fail' for c in r['checks']),r)
 def test_elf_got_accepted_but_real_forbidden_external_rejected(self):
  ident='c11/ex05'
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);shutil.copytree(ROOT/ident,p,dirs_exist_ok=True)
   good=check_exercise(p,ident,sandbox=True)
   self.assertEqual(good['result'],'passed',good)
   source=p/'helpers.c';s=source.read_text()
   s='#include <stdio.h>\n'+s
   # Ajoute un appel réellement externe et non autorisé sans supprimer le programme.
   s=s.replace('void\tft_text(char *s)\n{','void\tft_text(char *s)\n{\n\tputs("forbidden");')
   source.write_text(s)
   bad=check_exercise(p,ident,sandbox=True)
   self.assertEqual(bad['result'],'failed',bad)
   self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='fail' and 'puts' in c['message'] for c in bad['checks']),bad)

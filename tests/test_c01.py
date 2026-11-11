"""C 01 v6 : tests fonctionnels non officiels sur rendus de confiance."""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES, canonical_exercise
from moulinette import cli
from moulinette.dashboard import render_dashboard

ROOT=Path(__file__).resolve().parents[1]
NAMES=['ft_ft','ft_ultimate_ft','ft_swap','ft_div_mod','ft_ultimate_div_mod','ft_putstr','ft_strlen','ft_rev_int_tab','ft_sort_int_tab']
BAD=['void ft_ft(int *p) { (void)p; }',
     'void ft_ultimate_ft(int *********p) { (void)p; }',
     'void ft_swap(int *a, int *b) { (void)a; (void)b; }',
     'void ft_div_mod(int a, int b, int *d, int *m) { (void)a; (void)b; *d=0; *m=0; }',
     'void ft_ultimate_div_mod(int *a, int *b) { *a=0; *b=0; }',
     'void ft_putstr(char *s) { (void)s; }',
     'int ft_strlen(char *s) { (void)s; return 0; }',
     'void ft_rev_int_tab(int *a, int n) { (void)a; (void)n; }',
     'void ft_sort_int_tab(int *a, int n) { (void)a; (void)n; }']

class CatalogueC01(unittest.TestCase):
    def test_dashboard_lists_both_modules_and_total(self):
        html=render_dashboard({'recent':[],'latest':[],'count':0})
        self.assertIn('Parcours disponible',html);self.assertIn('0 <span>/ 109</span>',html)
        self.assertIn('c01/ex00',html);self.assertIn('c01/ex08',html)
    def test_nine_exercises_registered_with_pdf_version_and_restrictions(self):
        for i,name in enumerate(NAMES):
            ident=f'c01/ex{i:02}'
            with self.subTest(ident=ident):
                self.assertEqual(canonical_exercise('42/c/'+ident),ident)
                spec=EXERCISES[ident]
                self.assertEqual(spec['source'],name+'.c')
                self.assertEqual(spec['subject_version'],'6')
                self.assertEqual(spec['allowed_functions'],{'write'} if i==5 else set())

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'compilateur C et nm requis')
class FunctionalC01(unittest.TestCase):
    def test_reference_renditions_pass_and_wrong_ones_fail(self):
        for i,name in enumerate(NAMES):
            with self.subTest(exercise=i),patch('moulinette.checker.check_norm',return_value=('pass','témoin style')):
                spec=f'c01/ex{i:02}'
                report=check_exercise(ROOT/'exemples'/'c01'/f'ex{i:02}',spec)
                self.assertEqual(report['result'],'passed',report)
                self.assertEqual(report['subject_version'],'6')
                with tempfile.TemporaryDirectory() as t:
                    (Path(t)/(name+'.c')).write_text(BAD[i]+'\n')
                    bad=check_exercise(Path(t),spec)
                self.assertEqual(bad['result'],'failed',bad)
                self.assertTrue(any(c['status']=='fail' and c['name'].startswith('Test ') for c in bad['checks']),bad)
    def test_function_write_is_rejected_for_ft_ft(self):
        source='#include <unistd.h>\nvoid ft_ft(int *p) { write(1,"",0); *p=42; }\n'
        with tempfile.TemporaryDirectory() as t,patch('moulinette.checker.check_norm',return_value=('pass','témoin style')):
            (Path(t)/'ft_ft.c').write_text(source)
            r=check_exercise(Path(t),'c01/ex00')
        self.assertEqual(r['result'],'failed');self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='fail' for c in r['checks']))
    def test_wrong_prototype_and_extra_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as t,patch('moulinette.checker.check_norm',return_value=('pass','témoin')):
            p=Path(t);(p/'ft_ft.c').write_text('int ft_ft(int *p) { *p=42; return 0; }\n')
            r=check_exercise(p,'c01/ex00')
            self.assertEqual(r['result'],'failed');self.assertTrue(any(c['name']=='Prototype' and c['status']=='fail' for c in r['checks']))
            (p/'extra').write_text('')
            r=check_exercise(p,'c01/ex00');self.assertTrue(any(c['name']=='Fichiers supplémentaires' and c['status']=='fail' for c in r['checks']))

    def test_cli_c01_json_shows_correct_module_and_version(self):
        out=io.StringIO()
        with patch('moulinette.checker.check_norm',return_value=('pass','témoin style')),contextlib.redirect_stdout(out):
            result=cli.main(['check',str(ROOT/'exemples/c01/ex00'),'--exercise','c01/ex00','--unsafe-local','--no-history','--json'])
        self.assertEqual(result,0);data=json.loads(out.getvalue());self.assertEqual(data['exercise'],'42/c/c01/ex00');self.assertEqual(data['subject_version'],'6')

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('norminette') and shutil.which('cc') and shutil.which('nm'), 'bwrap, norminette, cc et nm requis')
class RealBubblewrapC01(unittest.TestCase):
    def test_all_nine_correct_examples_with_real_norm_and_launcher_validation(self):
        from moulinette.sandbox_doctor import diagnose
        from moulinette.cgroup_launcher import _validate_favorable_checks
        checks=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not checks or any(x['status']!='pass' for x in checks):self.skipTest('Bubblewrap indisponible')
        for i,name in enumerate(NAMES):
            with self.subTest(exercise=i):
                ident=f'c01/ex{i:02}'
                report=check_exercise(ROOT/'exemples'/'c01'/f'ex{i:02}',ident,sandbox=True)
                self.assertEqual(report['result'],'passed',report)
                self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in report['checks']))
                _validate_favorable_checks(ident,report['checks'])

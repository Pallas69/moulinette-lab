"""Explications pédagogiques, comparaisons et guide de style embarqué."""
import base64
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette.dashboard import render_dashboard
from moulinette.dashboard_insights import explanations, expected_signature, compare_checks
from moulinette.checker import check_exercise
from moulinette.history import read_history, store_attempt

ROOT=Path(__file__).resolve().parents[1]
DIAGNOSTIC="""ft_print_alphabet.c: In function 'main':
ft_print_alphabet.c:21:14: error: unused variable 'alpha' [-Werror=unused-variable]
ft_print_alphabet.c: In function 'my_print_alpha':
ft_print_alphabet.c:17:1: error: control reaches end of non-void function [-Werror=return-type]
cc1: all warnings being treated as errors
"""

def row(ex,checks,result='failed'):
    return {'exercise':ex,'created_at':'2026-01-02T10:00:00','source_label':'exemple',
            'isolation':'local','result':result,'checks':checks}

class DiagnosticTests(unittest.TestCase):
    def test_reported_user_compiler_messages_get_targeted_explanations(self):
        check={'name':'Compilation','status':'fail','message':DIAGNOSTIC}
        tips=explanations('c00/ex01',check)
        self.assertTrue(any('alpha' in t and 'jamais utilisée' in t and 'main' in t for t in tips),tips)
        self.assertTrue(any('my_print_alpha' in t and 'retourner une valeur' in t for t in tips),tips)
        self.assertTrue(any('void ft_print_alphabet(void);' in t and 'pas encore été vérifié' in t for t in tips),tips)
        self.assertTrue(any('main' in t and 'hors du fichier rendu' in t for t in tips),tips)
        html=render_dashboard({'count':1,'recent':[row('c00/ex01',[check])],'latest':[]})
        self.assertIn('Pour comprendre',html);self.assertIn('my_print_alpha',html)
        self.assertIn('void ft_print_alphabet(void);',html)

    def test_do_not_invent_function_variable_or_main(self):
        check={'name':'Compilation','status':'fail','message':'fatal error: source introuvable'}
        tips=explanations('c00/ex01',check)
        self.assertFalse(any('variable' in t or 'main' in t for t in tips),tips)
        self.assertTrue(any('pas encore été vérifié' in t for t in tips))
        self.assertEqual(explanations('c00/ex01',dict(check,status='pass')),[])
        self.assertEqual(explanations('c00/ex01',dict(check,name='Test X')),[])
        self.assertIsNone(expected_signature('c10/ex00'))

    def test_explanation_escapes_untrusted_compiler_text(self):
        check={'name':'Compilation','status':'fail','message':"In function 'main':\nerror: unused variable '<img>'\n<script>alert(1)</script>"}
        page=render_dashboard({'count':1,'recent':[row('c00/ex01',[check])],'latest':[]})
        self.assertNotIn('<script>alert(1)</script>',page)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',page)
        self.assertNotIn('variable « &lt;img&gt; »',page)

    @unittest.skipUnless(shutil.which('cc') and shutil.which('bwrap'), 'cc et bwrap requis')
    def test_real_compiler_failure_is_recorded_and_explained_on_dashboard(self):
        code=('int my_print_alpha(void)\n{\n}\n'
              'int main(void)\n{\n\tchar alpha;\n\treturn (0);\n}\n')
        with tempfile.TemporaryDirectory() as t, patch.dict('os.environ',{'XDG_DATA_HOME':t}):
            source=Path(t)/'soumission';source.mkdir();(source/'ft_print_alphabet.c').write_text(code)
            report=check_exercise(source,'c00/ex01',sandbox=True)
            self.assertEqual(report['result'],'failed',report)
            store_attempt(report,str(source));page=render_dashboard(read_history())
            self.assertIn('Pour comprendre',page);self.assertIn('alpha',page)
            self.assertIn('my_print_alpha',page);self.assertIn('void ft_print_alphabet(void);',page)
            self.assertNotIn('Style 42 adapté',page)

class ComparisonTests(unittest.TestCase):
    def test_compare_only_same_named_executed_unique_checks(self):
        old=row('c00/ex01',[{'name':'Compilation','status':'fail'}, {'name':'Test x','status':'pass'},
                            {'name':'Ambigu','status':'pass'},{'name':'Ambigu','status':'fail'},
                            {'name':'Norminette','status':'unavailable'}])
        new=row('c00/ex01',[{'name':'Compilation','status':'pass'},{'name':'Test x','status':'fail'},
                            {'name':'Ambigu','status':'pass'},{'name':'Norminette','status':'pass'},
                            {'name':'Nouveau','status':'pass'}])
        self.assertEqual(compare_checks(new,old),(['Compilation'],['Test x'],['Norminette']))
    def test_page_compares_same_exercise_and_labels_missing_comparisons(self):
        checks=lambda status:[{'name':'Compilation','status':status,'message':'diagnostic'}]
        new=row('c00/ex01',checks('pass'),'passed')
        different=row('c00/ex00',checks('fail'))
        old=row('c00/ex01',checks('fail'))
        page=render_dashboard({'count':3,'recent':[new,different,old],'latest':[new,different]})
        self.assertEqual(page.count('Comparaison avec la tentative précédente'),1)
        self.assertIn('De échec à réussi : Compilation',page)
        self.assertIn('une étape non exécutée n’est ni réussie ni échouée',page)
    def test_no_previous_no_comparison(self):
        one=row('c00/ex01',[{'name':'Compilation','status':'fail','message':'bad'}])
        page=render_dashboard({'count':1,'recent':[one],'latest':[one]})
        self.assertNotIn('Comparaison avec la tentative précédente',page)

class StyleGuideTests(unittest.TestCase):
    def test_all_four_embedded_pdfs_match_delivered_files(self):
        page=render_dashboard({'count':0,'recent':[],'latest':[]})
        decoded={}
        for kind,prefix in [('guide-utilisation','manuel-utilisateur'),('guide-style-c','guide-style-c')]:
            for theme in ('ocean','blanc'):
                with self.subTest(kind=kind,theme=theme):
                    match=re.search(rf'data-document="{kind}" data-theme="{theme}" href="data:application/pdf;base64,([^"]+)"',page)
                    self.assertIsNotNone(match)
                    pdf=base64.b64decode(match.group(1),validate=True)
                    self.assertEqual(pdf,(ROOT/'docs'/f'{prefix}-v0.32.8-{theme}.pdf').read_bytes())
                    self.assertEqual(pdf,(ROOT/'moulinette/assets'/f'{kind}-{theme}.pdf').read_bytes())
                    self.assertIn(b'LiberationSerif',pdf);self.assertIn(b'JetBrainsMono',pdf)
                    decoded[kind,theme]=pdf
        self.assertNotEqual(decoded['guide-style-c','ocean'],decoded['guide-style-c','blanc'])
        self.assertNotEqual(decoded['guide-utilisation','ocean'],decoded['guide-utilisation','blanc'])
    @unittest.skipUnless(shutil.which('norminette'),'Norminette requise')
    def test_guide_alphabet_source_against_real_norminette(self):
        import subprocess
        from moulinette.norm import parse_norm_result
        binary=shutil.which('norminette')
        version=subprocess.run([binary,'--version'],capture_output=True,timeout=10)
        if b'norminette 3.3.59' not in (version.stdout+version.stderr).lower():
            self.skipTest('Norminette 3.3.59 requise')
        text=(ROOT/'docs/guide-style-c.md').read_text()
        section=text.split('# 05 · Exemple : alphabet',1)[1]
        code=section.split('```c\n',1)[1].split('\n```',1)[0]+'\n'
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'ft_print_alphabet.c';source.write_text(code)
            result=subprocess.run([binary,'-f','json','--no-colors',str(source)],capture_output=True,timeout=15)
        status,message=parse_norm_result(result.stdout,result.returncode)
        self.assertEqual(status,'pass',(message,result.stderr))
        self.assertIn('INVALID_HEADER ignoré : 1',message)

    def test_source_names_norm_rules_and_nonofficial_limit(self):
        text=(ROOT/'docs/guide-style-c.md').read_text()
        for term in ('3.3.59','INVALID_HEADER','25 lignes','80 colonnes','tabulations',
                     'retourner','unused variable','ft_print_alphabet','non officiels','42School/norminette/3.3.59'):
            with self.subTest(term=term):self.assertIn(term,text)

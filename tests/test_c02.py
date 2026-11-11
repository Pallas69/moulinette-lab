"""C 02 v6 : correctifs pédagogiques non officiels, code de confiance uniquement."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.checker import check_exercise
from moulinette.exercise_catalog import EXERCISES, canonical_exercise
from moulinette.dashboard import render_dashboard
from moulinette import cli

ROOT=Path(__file__).resolve().parents[1]
NAMES=['ft_strcpy','ft_strncpy','ft_str_is_alpha','ft_str_is_numeric',
       'ft_str_is_lowercase','ft_str_is_uppercase','ft_str_is_printable',
       'ft_strupcase','ft_strlowcase','ft_strcapitalize','ft_strlcpy',
       'ft_putstr_non_printable','ft_print_memory']
BAD=['char *ft_strcpy(char *d,char *s) { (void)s; return d; }',
     'char *ft_strncpy(char *d,char *s,unsigned int n) { (void)s;(void)n; return d; }',
     'int ft_str_is_alpha(char *s) { (void)s; return 1; }',
     'int ft_str_is_numeric(char *s) { (void)s; return 1; }',
     'int ft_str_is_lowercase(char *s) { (void)s; return 1; }',
     'int ft_str_is_uppercase(char *s) { (void)s; return 1; }',
     'int ft_str_is_printable(char *s) { (void)s; return 1; }',
     'char *ft_strupcase(char *s) { return s; }',
     'char *ft_strlowcase(char *s) { return s; }',
     'char *ft_strcapitalize(char *s) { return s; }',
     'unsigned int ft_strlcpy(char *d,char *s,unsigned int n) { (void)d;(void)s;(void)n; return 0; }',
     'void ft_putstr_non_printable(char *s) { (void)s; }',
     'void *ft_print_memory(void *p,unsigned int n) { (void)n; return p; }']

class C02Catalog(unittest.TestCase):
    def test_pdf_names_versions_and_functions(self):
        for i,name in enumerate(NAMES):
            ident=f'c02/ex{i:02}'
            with self.subTest(ident=ident):
                self.assertEqual(canonical_exercise('42/c/'+ident),ident)
                spec=EXERCISES[ident]
                self.assertEqual(spec['source'],name+'.c')
                self.assertEqual(spec['subject_version'],'6')
                self.assertEqual(spec['allowed_functions'],{'write'} if i in (11,12) else set())
    def test_dashboard_exercises_and_total(self):
        page=render_dashboard({'recent':[],'latest':[],'count':0})
        self.assertIn('Parcours disponible',page)
        self.assertIn('0 <span>/ 109</span>',page)
        self.assertIn('c02/ex00',page);self.assertIn('c02/ex12',page)

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'),'compilateur C et nm requis')
class C02Functional(unittest.TestCase):
    def test_thirteen_reference_and_incorrect_examples(self):
        for i,name in enumerate(NAMES):
            with self.subTest(exercise=i),patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
                ident=f'c02/ex{i:02}'
                r=check_exercise(ROOT/'exemples'/'c02'/f'ex{i:02}',ident)
                self.assertEqual(r['result'],'passed',r)
                with tempfile.TemporaryDirectory() as t:
                    (Path(t)/(name+'.c')).write_text(BAD[i]+'\n')
                    r=check_exercise(Path(t),ident)
                self.assertEqual(r['result'],'failed',r)
                self.assertTrue(any(c['status']=='fail' and c['name'].startswith('Test ') for c in r['checks']),r)
    def test_forbidden_write_and_wrong_prototype(self):
        with tempfile.TemporaryDirectory() as t,patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
            p=Path(t);f=p/'ft_strcpy.c'
            f.write_text('#include <unistd.h>\nchar *ft_strcpy(char *d,char *s) { write(1,s,0); return d; }\n')
            r=check_exercise(p,'c02/ex00')
            self.assertTrue(any(c['status']=='fail' and c['name']=='Fonctions externes' for c in r['checks']),r)
            f.write_text('int ft_strcpy(char *d,char *s) { (void)d;(void)s; return 0; }\n')
            r=check_exercise(p,'c02/ex00')
            self.assertTrue(any(c['status']=='fail' and c['name']=='Prototype' for c in r['checks']),r)
    def test_nontrivial_faults_are_detected(self):
        mutations=[
            (1, 'char *ft_strncpy(char *d,char *s,unsigned int n) { unsigned int i=0; while(i<n && s[i]) {d[i]=s[i];i++;} return d; }'),
            (9, 'char *ft_strcapitalize(char *s) { int i=0,start=1; while(s[i]) { if(start && s[i]>=\'a\' && s[i]<=\'z\') s[i]-=32; else if(!start && s[i]>=\'A\' && s[i]<=\'Z\') s[i]+=32; start=!( (s[i]>=\'A\' && s[i]<=\'Z\') || (s[i]>=\'a\' && s[i]<=\'z\')); i++; } return s; }'),
            (10, 'unsigned int ft_strlcpy(char *d,char *s,unsigned int n) { unsigned int i=0; if(n) { while(i<n && s[i]) {d[i]=s[i];i++;} if(i<n) d[i]=0; } while(s[i])i++; return i; }'),
            (11, '#include <unistd.h>\nvoid ft_putstr_non_printable(char *s) { while(*s) write(1,s++,1); }'),
        ]
        with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
            for i,source in mutations:
                with self.subTest(exercise=i), tempfile.TemporaryDirectory() as t:
                    (Path(t)/(NAMES[i]+'.c')).write_text(source+'\n')
                    r=check_exercise(Path(t),f'c02/ex{i:02}')
                    self.assertTrue(any(c['status']=='fail' and c['name'].startswith('Test ') for c in r['checks']),r)

    def test_cli_json_subject(self):
        out=io.StringIO()
        with patch('moulinette.checker.check_norm',return_value=('pass','style simulé')),contextlib.redirect_stdout(out):
            rc=cli.main(['check',str(ROOT/'exemples/c02/ex00'),'--exercise','c02/ex00','--unsafe-local','--no-history','--json'])
        self.assertEqual(rc,0)
        data=json.loads(out.getvalue());self.assertEqual(data['exercise'],'42/c/c02/ex00');self.assertEqual(data['subject_version'],'6')
    def test_print_memory_accepts_uppercase_unpadded_address(self):
        import re
        source=(ROOT/'exemples/c02/ex12/ft_print_memory.c').read_text()
        replacement='''static void put_address(uintptr_t value)
{
    char out[2 * sizeof(value)]; char *hex="0123456789ABCDEF"; int i=0;
    do { out[i++]=hex[value % 16]; value/=16; } while(value);
    write(1,"0X",2);
    while(i) write(1,&out[--i],1);
    write(1,": ",2);
}
'''
        source,n=re.subn(r'static void\s+put_address\(uintptr_t value\)\n\{.*?\n\}\n',replacement,source,count=1,flags=re.S)
        self.assertEqual(n,1);source=source.replace('0123456789abcdef','0123456789ABCDEF')
        with tempfile.TemporaryDirectory() as t,patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
            (Path(t)/'ft_print_memory.c').write_text(source)
            r=check_exercise(Path(t),'c02/ex12')
        self.assertEqual(r['result'],'passed',r)

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('norminette') and shutil.which('cc') and shutil.which('nm'),'bwrap, norminette, cc et nm requis')
class C02RealBubblewrap(unittest.TestCase):
    def test_thirteen_examples_and_favorable_reports(self):
        from moulinette.sandbox_doctor import diagnose
        from moulinette.cgroup_launcher import _validate_favorable_checks
        checks=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not checks or any(x['status']!='pass' for x in checks):self.skipTest('Bubblewrap indisponible')
        for i in range(13):
            with self.subTest(exercise=i):
                ident=f'c02/ex{i:02}'
                r=check_exercise(ROOT/'exemples'/'c02'/f'ex{i:02}',ident,sandbox=True)
                self.assertEqual(r['result'],'passed',r)
                self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in r['checks']))
                _validate_favorable_checks(ident,r['checks'])

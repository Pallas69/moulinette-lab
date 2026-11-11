"""Une sortie nm inconnue ou tronquée ne doit pas être validée."""
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import checker

EXAMPLE = Path(__file__).resolve().parent.parent / 'exemples' / 'ft_print_comb'

@unittest.skipUnless(shutil.which('cc') and shutil.which('nm'), 'cc et nm requis')
class NmRobustnessTests(unittest.TestCase):
    def check_with_fake_nm(self, data):
        real_run=checker._run
        def run(cmd,*args,**kwargs):
            if len(cmd)>1 and cmd[1]=='-u': return (0,data,b'',False)
            return real_run(cmd,*args,**kwargs)
        with patch('moulinette.checker._run',side_effect=run), patch('moulinette.checker.check_norm',return_value=('pass','style simulé')):
            return checker.check_exercise(EXAMPLE,'c00/ex05')

    def test_malformed_line_is_unavailable_not_success(self):
        result=self.check_with_fake_nm(b'unknown tool output\n')
        self.assertEqual(result['result'],'incomplete',result)
        self.assertTrue(any(x['name']=='Fonctions externes' and x['status']=='unavailable' for x in result['checks']))

    def test_invalid_utf8_is_unavailable_not_success(self):
        result=self.check_with_fake_nm(b' U write\n\xff')
        self.assertEqual(result['result'],'incomplete',result)

    def test_truncated_output_is_unavailable_even_when_parsable_prefix(self):
        data=(b' U write\n' * ((checker.MAX_CAPTURE // 9)+1))[:checker.MAX_CAPTURE]
        self.assertEqual(len(data),checker.MAX_CAPTURE)
        result=self.check_with_fake_nm(data)
        self.assertEqual(result['result'],'incomplete',result)

    def test_valid_symbol_format_remains_accepted(self):
        result=self.check_with_fake_nm(b'                 U write\n')
        self.assertEqual(result['result'],'passed',result)


@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm'), 'bwrap, cc et nm requis')
class NmSandboxTests(unittest.TestCase):
    def test_bad_output_stops_sandbox_before_link_or_student_tests(self):
        from moulinette.sandbox_doctor import diagnose
        checks=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not checks or any(x['status']!='pass' for x in checks): raise unittest.SkipTest('Bubblewrap indisponible')
        real_runner=checker.ExperimentalRunner
        actions=[]
        class BadNmRunner:
            def __init__(self,*args,**kwargs): self.real=real_runner(*args,**kwargs)
            def __call__(self,cmd,*args,**kwargs):
                actions.append(cmd)
                if len(cmd)>1 and cmd[1]=='-u': return (0,b'format inattendu\n',b'',False)
                return self.real(cmd,*args,**kwargs)
        with patch('moulinette.checker.ExperimentalRunner',BadNmRunner):
            result=checker.check_exercise(EXAMPLE,'c00/ex05',sandbox=True)
        self.assertEqual(result['result'],'incomplete',result)
        self.assertTrue(any(x['name']=='Fonctions externes' and x['status']=='unavailable' for x in result['checks']))
        self.assertFalse(any('harness.c' in cmd for cmd in actions))
        self.assertFalse(any(x['name'].startswith('Test ') for x in result['checks']))

if __name__=='__main__': unittest.main()

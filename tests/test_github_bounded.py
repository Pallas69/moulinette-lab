"""Contrôles déterministes de l'enveloppe de récupération bornée."""
import base64
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette.github_source import GitHubSourceError, MAX_FILE
from moulinette.github_bounded import _parse_snapshot, bounded_public_repository

SHA='0123456789abcdef0123456789abcdef01234567'
URL='https://github.com/demo/example'
def payload():
    return {'version':1,'entries':['ft_putchar.c','interdit'], 'source_type':'file',
            'source_b64':base64.b64encode(b'example').decode(),
            'source':{'kind':'github','url':URL,'commit':SHA,'ref':'main','subdir':'c00/ex00'}}

class SnapshotValidationTests(unittest.TestCase):
    def parse(self, obj): return _parse_snapshot(obj,URL,'main','c00/ex00','ft_putchar.c')
    def test_valid_snapshot(self):
        self.assertEqual(self.parse(payload())['contents'],b'example')
    def test_rejects_bad_paths_duplicates_and_inconsistent_sources(self):
        cases=[dict(payload(),entries=['ft_putchar.c','../x']),dict(payload(),entries=['ft_putchar.c','bad/name']),
               dict(payload(),entries=['ft_putchar.c','ft_putchar.c']),dict(payload(),entries=['ft_putchar.c'],source_type='absent'),
               dict(payload(),entries=['extra'],source_type='file'),dict(payload(),entries=['ft_putchar.c'],source_type='symlink',source_b64='YQ=='),
               dict(payload(),entries=['ft_putchar.c','\x00']),dict(payload(),entries=['ft_putchar.c']*1001)]
        for x in cases:
            with self.subTest(case=x),self.assertRaises(GitHubSourceError): self.parse(x)
    def test_rejects_bad_identity_large_source_and_unknown_fields(self):
        for x in (dict(payload(),source=dict(payload()['source'],commit='bad')),
                  dict(payload(),source=dict(payload()['source'],url='https://evil.invalid/x')),
                  dict(payload(),source=dict(payload()['source'],ref='other')),
                  dict(payload(),source=dict(payload()['source'],subdir='../etc')),
                  dict(payload(),source_b64='%%bad'),dict(payload(),unexpected=True),
                  dict(payload(),source_b64=base64.b64encode(b'a'*(MAX_FILE+2)).decode())):
            with self.subTest(case=str(x)[:200]),self.assertRaises(GitHubSourceError): self.parse(x)
    def test_sha_request_requires_exact_match(self):
        with self.assertRaises(GitHubSourceError): _parse_snapshot(payload(),URL,'a'*40,'c00/ex00','ft_putchar.c')

class MaterializationTests(unittest.TestCase):
    def test_creates_bounded_stage_with_extras_and_cleans_up(self):
        with patch('moulinette.github_bounded._fetch_snapshot',return_value=payload()):
            with bounded_public_repository(URL,'c00/ex00',ref='main',subdir='c00/ex00') as (stage,source):
                parent=stage.parent
                self.assertEqual((stage/'ft_putchar.c').read_bytes(),b'example')
                self.assertEqual((stage/'interdit').read_bytes(),b'')
                self.assertEqual(source['commit'],SHA)
            self.assertFalse(parent.exists())
    def test_unsafe_source_symlink_remains_refused(self):
        from moulinette.checker import check_ex00
        data=dict(payload(),entries=['ft_putchar.c'],source_type='symlink',source_b64='')
        with patch('moulinette.github_bounded._fetch_snapshot',return_value=data):
            with bounded_public_repository(URL,'c00/ex00',ref='main',subdir='c00/ex00') as (stage,_):
                self.assertTrue((stage/'ft_putchar.c').is_symlink())
                self.assertEqual(check_ex00(stage)['result'],'failed')
    def test_oversized_source_stays_oversized_for_checker(self):
        from moulinette.checker import check_ex00
        data=dict(payload(),entries=['ft_putchar.c'],source_b64=base64.b64encode(b'x'*(MAX_FILE+1)).decode())
        with patch('moulinette.github_bounded._fetch_snapshot',return_value=data):
            with bounded_public_repository(URL,'c00/ex00',ref='main',subdir='c00/ex00') as (stage,_):
                report=check_ex00(stage)
        self.assertEqual(report['result'],'failed')
        self.assertTrue(any(c['name']=='Taille du fichier' for c in report['checks']))
    def test_invalid_before_fetch_and_no_fallback(self):
        with patch('moulinette.github_bounded._fetch_snapshot') as fetch:
            with self.assertRaises(GitHubSourceError):
                with bounded_public_repository(URL,'c00/ex00',subdir='../etc'): pass
            fetch.assert_not_called()
    def test_missing_bwrap_means_no_git_or_fallback(self):
        with patch('moulinette.github_bounded.shutil.which',return_value=None), \
             patch('moulinette.github_source._git',side_effect=AssertionError('pas de Git sur hôte')):
            with self.assertRaises(GitHubSourceError):
                with bounded_public_repository(URL,'c00/ex00'): pass

class BubblewrapCommandTests(unittest.TestCase):
    def fake_capture(self, *, bad_status=False, code=0, output=None):
        import json
        from moulinette.github_bounded import _fetch_snapshot
        if output is None: output=json.dumps(payload()).encode()
        def fake(command,cwd,timeout,env,setup_limits,**kwargs):
            self.command=command; self.options=kwargs
            with patch('resource.setrlimit') as set_limit:
                setup_limits()
                self.limit_calls=set_limit.call_args_list
            status=b'{"child-pid":123}\n{"exit-code":1}\n' if bad_status else b'{"child-pid":123}\n{"exit-code":0}\n'
            os.write(kwargs['pass_fds'][0],status)
            return code,output,b'',False
        with patch('moulinette.github_bounded.shutil.which',return_value='/usr/bin/bwrap'), \
             patch('moulinette.github_bounded.run_bounded',side_effect=fake):
            return _fetch_snapshot(URL+'.git','c00/ex00','main','c00/ex00')
    def test_command_uses_one_bounded_tmpfs_no_host_workdir_and_shared_network(self):
        from moulinette.github_bounded import GIT_TMPFS_BYTES,MAX_WORKER_OUTPUT
        self.assertEqual(self.fake_capture(),payload())
        cmd=self.command
        self.assertIn('--share-net',cmd);self.assertIn('--unshare-all',cmd)
        ix=cmd.index('--tmpfs');self.assertEqual(cmd[ix-2:ix+2],['--size',str(GIT_TMPFS_BYTES),'--tmpfs','/work'])
        self.assertEqual(cmd.count('--tmpfs'),1)
        self.assertNotIn('--bind',cmd);self.assertIn('--ro-bind',cmd)
        self.assertEqual(self.options['max_stdout'],MAX_WORKER_OUTPUT)
    def test_worker_limits_cpu_and_does_not_mount_entire_package(self):
        import resource
        self.fake_capture()
        pairs=[tuple(c.args) for c in self.limit_calls]
        self.assertIn((resource.RLIMIT_CPU,(30,46)),pairs)
        cmd=self.command
        self.assertNotIn(str(Path(__file__).resolve().parents[1]/'moulinette'),cmd)
        self.assertIn('/app/moulinette/github_worker.py',cmd)

    def test_bad_status_rejected(self):
        with self.assertRaises(GitHubSourceError):self.fake_capture(bad_status=True)
    def test_uncertain_output_rejected(self):
        with self.assertRaises(GitHubSourceError):self.fake_capture(output=b'not json')
    def test_duplicate_keys_and_nonstandard_numbers_rejected(self):
        for message in (b'{"version":1,"version":1}', b'{"version":NaN}'):
            with self.subTest(message=message),self.assertRaises(GitHubSourceError):
                self.fake_capture(output=message)
    def test_deeply_nested_json_is_rejected_as_unavailable(self):
        with self.assertRaises(GitHubSourceError): self.fake_capture(output=b'['*10000+b']'*10000)
    def test_bwrap_failure_is_not_fallback(self):
        with self.assertRaises(GitHubSourceError):self.fake_capture(code=1)

@unittest.skipUnless(__import__('shutil').which('bwrap'), 'Bubblewrap requis')
class TmpfsIntegrationTests(unittest.TestCase):
    def test_real_tmpfs_caps_total_of_multiple_files(self):
        from moulinette.sandbox_doctor import diagnose
        relevant=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not relevant or any(x['status']!='pass' for x in relevant): raise unittest.SkipTest('Bubblewrap indisponible')
        import shutil,subprocess
        bwrap=shutil.which('bwrap')
        code=("import errno,os\n"
              "f=os.statvfs('/work');print('capacity',f.f_blocks*f.f_frsize,flush=True)\n"
              "block=b'x'*1048576\n"
              "try:\n"
              " for name in ('a','b'):\n"
              "  with open('/work/'+name,'wb',buffering=0) as out:\n"
              "   for i in range(9):out.write(block)\n"
              "except OSError as e:\n"
              " print('errno',e.errno,flush=True)\n"
              "else: print('unexpected',flush=True)\n")
        cmd=[bwrap,'--unshare-all','--die-with-parent','--ro-bind','/usr','/usr',
             '--symlink','usr/lib','/lib','--size',str(16*1024*1024),'--tmpfs','/work',
             '--','/usr/bin/python3','-I','-B','-c',code]
        if Path('/usr/lib64').exists():cmd[cmd.index('--size'):cmd.index('--size')]=['--symlink','usr/lib64','/lib64']
        result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn(b'capacity 16777216',result.stdout)
        import errno
        self.assertIn(('errno '+str(errno.ENOSPC)).encode(),result.stdout)

class NewCliRoutingTests(unittest.TestCase):
    def test_cli_uses_bounded_stage_and_preserves_json_provenance(self):
        import json
        from moulinette import cli
        data=dict(payload(),entries=['ft_putchar.c'])
        def checker(path,sandbox=False):
            self.assertTrue(sandbox);self.assertEqual((path/'ft_putchar.c').read_bytes(),b'example')
            return {'exercise':'42/c/c00/ex00','result':'passed','checks':[],'isolation':'témoin'}
        out=io.StringIO()
        with patch('moulinette.github_bounded._fetch_snapshot',return_value=data) as fetch, \
             patch('moulinette.cli.check_ex00',side_effect=checker),contextlib.redirect_stdout(out):
            status=cli.main(['check',URL,'--exercise','c00/ex00','--experimental-sandbox','--trust-github',
                             '--ref','main','--subdir','c00/ex00','--no-history','--json'])
        self.assertEqual(status,0);fetch.assert_called_once()
        self.assertEqual(json.loads(out.getvalue())['source']['commit'],SHA)

    def test_cli_missing_bwrap_never_runs_correction(self):
        import json
        from moulinette import cli
        out=io.StringIO()
        with patch('moulinette.github_bounded.shutil.which',return_value=None), \
             patch('moulinette.cli.check_ex00',side_effect=AssertionError('aucun correcteur')), \
             contextlib.redirect_stdout(out):
            status=cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local','--trust-github','--no-history','--json'])
        self.assertEqual(status,2);self.assertEqual(json.loads(out.getvalue())['result'],'incomplete')

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch

from moulinette import cli
from moulinette.github_source import (GitHubSourceError, normalize_url, normalize_ref,
                                      normalize_subdir, trusted_public_repository as _unsafe_internal_repository, MAX_FILE, _git)
trusted_public_repository=partial(_unsafe_internal_repository, _allow_unbounded_environment=True)
from moulinette.history import read_history
from moulinette.dashboard import render_dashboard

URL='https://github.com/Trusted/example'
COMMIT='0123456789abcdef0123456789abcdef01234567'
FIXTURE=Path(__file__).resolve().parents[1]/'exemples'/'ft_putchar'/'ft_putchar.c'

class ValidationTests(unittest.TestCase):
    def test_valid_urls_are_canonical(self):
        for u in (URL,URL+'/',URL+'.git','https://GITHUB.COM/Trusted/example.git'):
            self.assertEqual(normalize_url(u)[0],URL+'.git')

    def test_rejects_non_github_credentials_ports_paths_and_options(self):
        for u in ('http://github.com/a/b','https://alice:password@github.com/a/b',
                  'https://github.com:443/a/b','https://github.com.evil.invalid/a/b',
                  'https://github.com/a/b/tree/main','https://github.com/a/../b',
                  'https://github.com/a/b?x=1','https://github.com/a/b#main',
                  'https://github.com/a/%62','https://github.com/a/-x.git\n',
                  'git@github.com:a/b.git','file:///tmp/repo','https://github.com/a/..'):
            with self.subTest(u=u),self.assertRaises(GitHubSourceError): normalize_url(u)

    def test_refs_and_path_are_restricted(self):
        for ref in ('main','feature/test','v1.2',COMMIT): self.assertEqual(normalize_ref(ref),ref)
        for ref in ('-oProxyCommand=evil','../foo','foo/../bar','bad name','x.lock','a//b','bad~1','12345678'):
            with self.subTest(ref=ref),self.assertRaises(GitHubSourceError): normalize_ref(ref)
        for path in ('/tmp/x','../x','ex/../x','./x','ex//x','ex\\evil','.git/config','a/\n'):
            with self.subTest(path=path),self.assertRaises(GitHubSourceError): normalize_subdir(path)
        self.assertEqual(normalize_subdir('c00/ex00'),('c00','ex00'))

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.env=patch.dict(os.environ,{'XDG_DATA_HOME':self.tmp.name,'GIT_CONFIG_COUNT':'1',
                                      'GIT_CONFIG_KEY_0':'url.file:///tmp/.insteadOf',
                                      'GIT_CONFIG_VALUE_0':'https://github.com/'})
        self.env.start();self.addCleanup(self.env.stop)
        self.calls=[];self.extra=False;self.source='normal';self.subdir='c00/ex00';self.git_failure=False
        self.git_patch=patch('moulinette.github_source._git',side_effect=self.fake_git)
        self.git_patch.start();self.addCleanup(self.git_patch.stop)
        # Ce groupe teste l'ancien adaptateur et le dispatch via un double ;
        # l'enveloppe tmpfs est testée séparément dans test_github_bounded.py.
        from moulinette.github_source import trusted_public_repository as in_process_fixture
        cli_patch=patch('moulinette.cli.trusted_public_repository',partial(in_process_fixture,_allow_unbounded_environment=True))
        cli_patch.start();self.addCleanup(cli_patch.stop)

    def fake_git(self,args,cwd,git,env):
        self.calls.append((list(args),dict(env)))
        if self.git_failure: raise GitHubSourceError('réseau indisponible')
        if args[0]=='clone':
            repo=Path(args[-1]);repo.mkdir();(repo/'.git').mkdir()
            target=repo/self.subdir;target.mkdir(parents=True,exist_ok=True)
            source=target/'ft_putchar.c'
            if self.source=='normal': source.write_bytes(FIXTURE.read_bytes())
            elif self.source=='oversize': source.write_bytes(b'a'*(MAX_FILE+100))
            elif self.source=='symlink': source.symlink_to('/etc/passwd')
            elif self.source=='directory': source.mkdir()
            if self.extra: (target/'interdit.txt').write_bytes(b'extra')
        if args[0]=='rev-parse': return COMMIT
        return ''

    def test_branch_subdir_metadata_and_cleanup(self):
        with trusted_public_repository(URL,'c00/ex00',ref='feature/exercise',subdir='c00/ex00') as (stage,meta):
            self.assertEqual((stage/'ft_putchar.c').read_bytes(),FIXTURE.read_bytes())
            self.assertEqual(meta,{'kind':'github','url':URL,'commit':COMMIT,'ref':'feature/exercise','subdir':'c00/ex00'})
            self.assertTrue(stage.exists());tmp_root=stage.parent
            self.assertIn('--branch',self.calls[0][0]);self.assertIn('feature/exercise',self.calls[0][0])
            self.assertEqual(self.calls[0][1]['GIT_CONFIG_GLOBAL'],'/dev/null')
            self.assertNotIn('GIT_CONFIG_COUNT',self.calls[0][1])
            self.assertEqual(self.calls[0][1]['GIT_TERMINAL_PROMPT'],'0')
        self.assertFalse(tmp_root.exists())

    def test_sha_fetch_checkout_and_matching(self):
        with trusted_public_repository(URL,'c00/ex00',ref=COMMIT,subdir='c00/ex00') as (_,meta):
            self.assertEqual(meta['commit'],COMMIT)
        self.assertEqual([c[0][0] for c in self.calls],['clone','fetch','checkout','rev-parse'])
        with self.assertRaises(GitHubSourceError):
            with trusted_public_repository(URL,'c00/ex00',ref='a'*40,subdir='c00/ex00'): pass

    def test_head_is_not_a_branch_and_extra_names_are_preserved(self):
        self.extra=True
        with trusted_public_repository(URL,'c00/ex00',ref='HEAD',subdir='c00/ex00') as (stage,_):
            self.assertEqual({p.name for p in stage.iterdir()},{'ft_putchar.c','interdit.txt'})
            self.assertEqual((stage/'interdit.txt').stat().st_size,0)
        self.assertNotIn('--branch',self.calls[0][0])

    def test_root_git_metadata_is_excluded_but_extras_not_hidden(self):
        self.subdir='.';self.extra=True
        with trusted_public_repository(URL,'c00/ex00') as (stage,_):
            self.assertEqual({p.name for p in stage.iterdir()},{'ft_putchar.c','interdit.txt'})

    def test_symlink_source_refused_by_checker(self):
        self.source='symlink'
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            status=cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local','--trust-github',
                             '--subdir','c00/ex00','--json','--no-history'])
        self.assertNotEqual(status,0);self.assertNotEqual(json.loads(output.getvalue())['result'],'passed')

    def test_large_source_is_still_large_and_extra_is_not_hidden(self):
        self.source='oversize';self.extra=True
        with trusted_public_repository(URL,'c00/ex00',subdir='c00/ex00') as (stage,_):
            self.assertEqual((stage/'ft_putchar.c').stat().st_size,MAX_FILE+1)
            self.assertTrue((stage/'interdit.txt').exists())

    def test_subdirectory_symlink_never_followed(self):
        def fake(args,cwd,git,env):
            if args[0]=='clone':
                repo=Path(args[-1]);repo.mkdir();(repo/'.git').mkdir();(repo/'out').symlink_to('/tmp')
            return COMMIT if args[0]=='rev-parse' else ''
        with patch('moulinette.github_source._git',side_effect=fake),self.assertRaises(GitHubSourceError):
            with trusted_public_repository(URL,'c00/ex00',subdir='out'): pass

    def test_cli_no_trust_means_no_git_no_correction(self):
        with contextlib.redirect_stderr(io.StringIO()),patch('moulinette.cli.check_ex00') as checker:
            code=cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local'])
        self.assertEqual(code,2);self.assertFalse(self.calls);checker.assert_not_called()

    def test_cli_json_history_and_no_history(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local','--trust-github','--subdir','c00/ex00','--json'])
        report=json.loads(output.getvalue());self.assertEqual(report['source']['commit'],COMMIT)
        self.assertIn(code,(0,2))  # la Norminette réelle peut manquer sur la machine
        self.assertTrue(any(x['name']=='Compilation' and x['status']=='pass' for x in report['checks']))
        history=read_history();self.assertEqual(history['count'],1)
        self.assertIn(COMMIT,history['recent'][0]['source_label'])
        self.assertIn('c00/ex00',history['recent'][0]['source_label'])
        self.assertIn(COMMIT,render_dashboard(history))
        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local','--trust-github','--subdir','c00/ex00','--no-history'])
        self.assertEqual(read_history()['count'],1)

    def test_extra_file_stops_correction(self):
        self.extra=True;output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local','--trust-github',
                           '--subdir','c00/ex00','--json','--no-history'])
        report=json.loads(output.getvalue())
        self.assertEqual(code,1);self.assertEqual(report['result'],'failed')
        self.assertFalse(any(x['name']=='Compilation' for x in report['checks']))

    def test_git_failure_is_incomplete_and_never_calls_checker(self):
        self.git_failure=True;output=io.StringIO()
        with contextlib.redirect_stdout(output),patch('moulinette.cli.check_ex00') as checker:
            code=cli.main(['check',URL,'--exercise','c00/ex00','--unsafe-local','--trust-github','--json'])
        self.assertEqual(code,2);self.assertEqual(json.loads(output.getvalue())['result'],'incomplete');checker.assert_not_called()

    def test_cgroup_dispatch_receives_staged_local_path(self):
        captured=[]
        def launch(path,exercise):
            captured.append((path,exercise,Path(path,'ft_putchar.c').read_bytes()))
            return {'exercise':'42/c/c00/ex00','result':'passed','checks':[],'isolation':'simulée'},None
        with patch('moulinette.cli.launch_cgroup',side_effect=launch),contextlib.redirect_stdout(io.StringIO()):
            status=cli.main(['check',URL,'--exercise','c00/ex00','--experimental-cgroup-sandbox',
                             '--trust-github','--subdir','c00/ex00','--no-history'])
        self.assertEqual(status,0);self.assertEqual(captured[0][1],'c00/ex00')
        self.assertEqual(captured[0][2],FIXTURE.read_bytes());self.assertFalse(Path(captured[0][0]).exists())

class GitProcessTests(unittest.TestCase):
    def test_git_command_disables_redirects_hooks_and_uses_bounded_capture(self):
        with tempfile.TemporaryDirectory() as tmp, patch('moulinette.github_source.run_bounded',return_value=(0,b'',b'',False)) as capture:
            self.assertEqual(_git(['rev-parse','HEAD'],Path(tmp),'/usr/bin/git',{'PATH':'/usr/bin:/bin'}),'')
        cmd=capture.call_args.args[0];kwargs=capture.call_args.kwargs
        self.assertIn('protocol.allow=never',cmd);self.assertIn('protocol.https.allow=always',cmd)
        self.assertIn('http.followRedirects=false',cmd);self.assertIn('core.hooksPath=/dev/null',cmd)
        self.assertEqual(kwargs['max_stdout'],4097);self.assertEqual(kwargs['max_stderr'],2049)

    def test_startup_error_is_incomplete_source_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch('moulinette.github_source.run_bounded',side_effect=subprocess.SubprocessError('limite impossible')):
            with self.assertRaises(GitHubSourceError): _git(['status'],Path(tmp),'/usr/bin/git',{})

    def test_timeout_is_source_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch('moulinette.github_source.run_bounded',return_value=(-9,b'',b'',True)):
            with self.assertRaises(GitHubSourceError): _git(['clone'],Path(tmp),'/usr/bin/git',{})

    def test_cleanup_uncertainty_is_source_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch('moulinette.github_source.run_bounded',side_effect=OSError('nettoyage non confirmé')):
            with self.assertRaises(GitHubSourceError): _git(['clone'],Path(tmp),'/usr/bin/git',{})

    def test_oversized_git_output_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, patch('moulinette.github_source.run_bounded',return_value=(0,b'a'*4097,b'',False)):
            with self.assertRaises(GitHubSourceError): _git(['rev-parse','HEAD'],Path(tmp),'/usr/bin/git',{})

    def test_temporary_directory_failure_is_source_error(self):
        with patch('moulinette.github_source.tempfile.TemporaryDirectory',side_effect=OSError('disque indisponible')):
            with self.assertRaises(GitHubSourceError):
                with trusted_public_repository(URL,'c00/ex00'): pass

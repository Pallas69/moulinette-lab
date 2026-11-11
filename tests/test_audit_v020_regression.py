"""Régressions basées sur une lecture critique de l'audit v0.20-dev."""
import contextlib
import io
import os
import subprocess
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
from moulinette.github_source import GitHubSourceError, trusted_public_repository
from moulinette.history import HistoryError, data_directory, read_history
from moulinette.dashboard import write_dashboard
from moulinette.process_capture import run_bounded

class DirectGitTests(unittest.TestCase):
    def test_direct_unbounded_helper_requires_explicit_internal_override(self):
        with patch('moulinette.github_source._git',side_effect=AssertionError('Git ne doit pas démarrer')):
            with self.assertRaises(GitHubSourceError):
                with trusted_public_repository('https://github.com/demo/example','c00/ex00'):pass

class ProcessInterruptTests(unittest.TestCase):
    def test_keyboard_interrupt_survives_cleanup_timeout_and_sends_kill_first(self):
        r1,w1=os.pipe();r2,w2=os.pipe();os.close(w1);os.close(w2)
        fake=MagicMock(pid=654321,stdout=os.fdopen(r1,'rb',buffering=0),stderr=os.fdopen(r2,'rb',buffering=0))
        calls=[]
        fake.wait.side_effect=lambda **kwargs: (calls.append('wait'), (_ for _ in ()).throw(subprocess.TimeoutExpired('x',0.5)))[1]
        def kill(*a):calls.append('kill')
        with patch('moulinette.process_capture.subprocess.Popen',return_value=fake), \
             patch('moulinette.process_capture.os.waitid',side_effect=KeyboardInterrupt), \
             patch('moulinette.process_capture.os.killpg',side_effect=kill):
            with self.assertRaises(KeyboardInterrupt) as got:
                run_bounded(['fixture'],Path('/tmp'),1,{},lambda:None)
        self.assertEqual(calls,['kill','wait'])
        self.assertIn('non confirmé',str(getattr(got.exception,'_moulinette_cleanup_error','')))

class HistoryPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        env=patch.dict(os.environ,{'XDG_DATA_HOME':self.tmp.name});env.start();self.addCleanup(env.stop)
    def test_database_hardlink_rejected_without_modification(self):
        dir=data_directory();dir.mkdir(); target=Path(self.tmp.name)/'existing'
        db=sqlite3.connect(target)
        try: db.execute('CREATE TABLE marker (x INTEGER)');db.commit()
        finally: db.close()
        before=target.read_bytes();os.link(target,dir/'history.sqlite3')
        with self.assertRaises(HistoryError):read_history()
        self.assertEqual(target.read_bytes(),before)
    def test_data_directory_symlink_rejected(self):
        target=Path(self.tmp.name)/'other';target.mkdir();data_directory().symlink_to(target,target_is_directory=True)
        with self.assertRaises(HistoryError):read_history()
        self.assertEqual(list(target.iterdir()),[])
    def test_dashboard_destination_symlink_rejected(self):
        read_history();target=Path(self.tmp.name)/'victim';target.write_text('untouched')
        link=data_directory()/'dashboard.html';link.symlink_to(target)
        with self.assertRaises((OSError,HistoryError)):write_dashboard()
        self.assertTrue(link.is_symlink());self.assertEqual(target.read_text(),'untouched')

class RequiredReportChecksTests(unittest.TestCase):
    def test_required_controls_are_not_duplicated_but_extra_warnings_may_repeat(self):
        from moulinette.cgroup_launcher import _validate_favorable_checks, _required_passes
        from moulinette.scope_protocol import ScopeProtocolError
        checks=[{'name':name,'status':'pass'} for name in _required_passes('c00/ex00')]
        checks += [{'name':'Fonctions externes','status':'info'},
                   {'name':'Sortie stderr','status':'info'}, {'name':'Sortie stderr','status':'info'}]
        _validate_favorable_checks('c00/ex00',checks)
        for duplicated in (checks[0], {'name':'Fonctions externes','status':'info'}):
            with self.subTest(duplicated=duplicated),self.assertRaises(ScopeProtocolError):
                _validate_favorable_checks('c00/ex00',checks+[duplicated])

if __name__=='__main__': unittest.main()

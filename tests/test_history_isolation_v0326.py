"""Régressions ciblées, bases factices uniquement ; aucun test de charge."""
import contextlib
import http.client
import io
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from moulinette import cli, live
from moulinette.history import read_history, store_attempt, read_unlocked_piscines
from moulinette.dashboard import write_dashboard


def report(ex='c01/ex00', result='passed'):
    return {'exercise':ex,'result':result,'checks':[], 'isolation':'test'}

class HistoryIsolationAndResetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.default=self.root/'default'; self.custom=self.root/'custom'/'history.sqlite3'
        self.patch=patch.dict(os.environ,{'XDG_DATA_HOME':str(self.default)});self.patch.start();self.addCleanup(self.patch.stop)
        store_attempt(report('c00/ex00'),'/ex/default')
        store_attempt(report('c01/ex00'),'/ex/custom',db_path=self.custom)
        with contextlib.closing(sqlite3.connect(self.custom)) as c, c:
            c.execute("INSERT INTO piscine_unlocks VALUES ('cpp','2026-01-01')")

    def test_static_db_reads_only_selected_and_retains_unlock_after_regression(self):
        store_attempt(report('c01/ex00','failed'),'/ex/regression',db_path=self.custom)
        default_db=self.default/'moulinette-lab/history.sqlite3'; before=default_db.read_bytes()
        default_html=write_dashboard(); prior=default_html.read_bytes()
        page=write_dashboard(db_path=self.custom)
        self.assertNotEqual(default_html,page); self.assertEqual(default_html.read_bytes(),prior)
        self.assertEqual(default_db.read_bytes(),before)
        self.assertEqual(read_history(db_path=self.custom)['count'],2)
        self.assertEqual(read_unlocked_piscines(read_history(db_path=self.custom),db_path=self.custom),{'c','cpp'})
        self.assertEqual(read_unlocked_piscines(read_history()),{'c'})
        text=page.read_text();self.assertIn('data-active-piscine="cpp"',text)
        self.assertNotIn('data-live-token="tok-default"', text)

    def test_custom_static_never_uses_default_daemon_or_creates_default_db(self):
        other=self.root/'empty-default'
        with patch.dict(os.environ, {'XDG_DATA_HOME':str(other)}), \
             patch('moulinette.live.read_live_daemon',return_value=(12345,'tok-default')):
            page=write_dashboard(db_path=self.custom)
            text=page.read_text()
        self.assertIn('data-live-token=""',text)
        self.assertNotIn('tok-default',text)
        self.assertFalse((other/'moulinette-lab/history.sqlite3').exists())
        self.assertFalse((other/'moulinette-lab/live-daemon.json').exists())

    def test_reset_confirmation_and_backup_of_selected_db(self):
        default_db=self.default/'moulinette-lab/history.sqlite3'; before=default_db.read_bytes()
        with patch('builtins.input',return_value='NON'),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reset','--db',str(self.custom)]),2)
        self.assertEqual(read_history(db_path=self.custom)['count'],1)
        self.assertFalse(list(self.custom.parent.glob('*.sauvegarde-*.sqlite3')))
        with patch('builtins.input',return_value='RESET'),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(['reset','--db',str(self.custom)]),0)
        self.assertIn('Sauvegarde',out.getvalue())
        backups=list(self.custom.parent.glob('*.sauvegarde-*.sqlite3'));self.assertEqual(len(backups),1)
        self.assertEqual(read_history(db_path=self.custom)['count'],0)
        self.assertEqual(read_unlocked_piscines(read_history(db_path=self.custom),db_path=self.custom),{'c'})
        self.assertEqual(read_history(db_path=backups[0])['count'],1)
        self.assertEqual(read_unlocked_piscines(read_history(db_path=backups[0]),db_path=backups[0]),{'c','cpp'})
        self.assertEqual(default_db.read_bytes(),before)
        self.assertEqual(backups[0].stat().st_mode & 0o777,0o600)

    def test_reset_no_confirmation_in_noninteractive_and_yes(self):
        with patch('builtins.input',side_effect=EOFError),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reset','--db',str(self.custom)]),2)
        self.assertEqual(read_history(db_path=self.custom)['count'],1)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reset','--db',str(self.custom),'--yes']),0)
        self.assertEqual(read_history(db_path=self.custom)['count'],0)

    def test_backup_failure_does_not_clear_database(self):
        with patch('moulinette.history.tempfile.mkstemp',side_effect=OSError('simulation')),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(['reset','--db',str(self.custom),'--yes']),2)
        self.assertEqual(read_history(db_path=self.custom)['count'],1)
        self.assertIn('cpp',read_unlocked_piscines(read_history(db_path=self.custom),db_path=self.custom))

    def test_default_reset_affects_default_only_and_preserves_backup(self):
        before=self.custom.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['reset','--yes']),0)
        self.assertEqual(read_history()['count'],0)
        self.assertEqual(self.custom.read_bytes(),before)
        backup=list((self.default/'moulinette-lab').glob('history.sqlite3.sauvegarde-*.sqlite3'))
        self.assertEqual(len(backup),1);self.assertEqual(read_history(db_path=backup[0])['count'],1)

    def test_reset_missing_and_foreign_db_do_not_create_or_modify(self):
        missing=self.root/'missing.sqlite3';foreign=self.root/'foreign.sqlite3'
        with contextlib.closing(sqlite3.connect(foreign)) as c, c:
            c.execute('CREATE TABLE other (value TEXT)')
            c.execute("INSERT INTO other VALUES ('keep')")
        before=foreign.read_bytes()
        for target in (missing,foreign):
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(['reset','--db',str(target),'--yes']),2)
        self.assertFalse(missing.exists()); self.assertEqual(foreign.read_bytes(),before)

    def test_reset_preserves_wal_data_in_backup(self):
        with contextlib.closing(sqlite3.connect(self.custom)) as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute("INSERT INTO piscine_unlocks VALUES ('py','2026-01-02')"); c.commit()
            from moulinette.history import reset_history
            backup=reset_history(self.custom)
            self.assertEqual(read_history(db_path=backup)['count'],1)
            self.assertEqual(read_unlocked_piscines(read_history(db_path=backup),db_path=backup),{'c','cpp','py'})
        self.assertEqual(read_history(db_path=self.custom)['count'],0)

    def test_custom_live_does_not_replace_default_daemon_or_default_dashboard(self):
        default_dir=self.default/'moulinette-lab';default_dir.mkdir(parents=True,exist_ok=True)
        statefile=default_dir/'live-daemon.json';statefile.write_text('default-marker')
        default_page=default_dir/'dashboard.html';default_page.write_text('default-page')
        class DummyServer:
            daemon_threads=False
            server_address=('127.0.0.1',12345)
            def serve_forever(self): pass
            def server_close(self): pass
        with patch('moulinette.live.ThreadingHTTPServer',return_value=DummyServer()):
            live.serve(open_browser=False,announce=lambda x: None,db_path=self.custom)
        self.assertEqual(statefile.read_text(),'default-marker')
        self.assertEqual(default_page.read_text(),'default-page')

    def test_live_selected_database_get_and_correction_do_not_touch_default(self):
        default_db=self.default/'moulinette-lab/history.sqlite3'; before=default_db.read_bytes()
        token='test-token';state={'runs':{},'active':None,'lock':threading.Lock()}
        server=ThreadingHTTPServer(('127.0.0.1',0),live.make_handler(token,state,db_path=self.custom))
        server.daemon_threads=True;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        def request(method,path,body=None):
            c=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=10)
            data=json.dumps(body).encode() if body is not None else None
            c.request(method,path,body=data,headers={'X-Moulinette-Token':token})
            res=c.getresponse();out=res.read();c.close();return res.status,out
        status,body=request('GET','/api/history');self.assertEqual(status,200);self.assertEqual(json.loads(body)['count'],1)
        status,body=request('GET','/?t='+token);self.assertEqual(status,200);self.assertIn(b'data-active-piscine="cpp"',body)
        folder=self.root/'rendu';folder.mkdir();(folder/'ft_ft.c').write_text('/* test non exécuté */')
        fake=report('c01/ex01','failed')
        with patch('moulinette.live.check_exercise',return_value=fake):
            status,body=request('POST','/api/run',{'exercise':'c01/ex01','path':str(folder),'mode':'bubblewrap'})
            self.assertEqual(status,202)
            run=json.loads(body)['run'];status,body=request('GET','/api/events?t='+token+'&run='+run)
            self.assertEqual(status,200);self.assertIn(b'"history": true',body)
        self.assertEqual(read_history(db_path=self.custom)['count'],2)
        self.assertEqual(default_db.read_bytes(),before)
        self.assertEqual(read_history()['count'],1)

if __name__ == '__main__': unittest.main()

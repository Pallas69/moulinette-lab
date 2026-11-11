import contextlib
import io
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import cli
from moulinette.history import HistoryError, data_directory, read_history, score, store_attempt
from moulinette.dashboard import render_dashboard, write_dashboard


def report(ex='c00/ex00', result='passed', checks=None):
    if checks is None:
        checks=[{'name':'Compilation','status':'pass','message':'ok'}, {'name':'Test','status':'pass','message':'ok'}]
    return {'exercise':'42/c/'+ex,'result':result,'checks':checks,'isolation':'Bubblewrap expérimental'}

class HistoryDashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        env=patch.dict(os.environ,{'XDG_DATA_HOME':self.tmp.name})
        env.start(); self.addCleanup(env.stop)

    def test_empty_history_is_real_empty_and_files_private(self):
        result=read_history(); self.assertEqual(result,{'count':0,'recent':[],'latest':[]})
        self.assertEqual(stat.S_IMODE(data_directory().stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((data_directory()/'history.sqlite3').stat().st_mode),0o600)
        page=write_dashboard(); text=page.read_text()
        self.assertIn('Aucune correction enregistrée',text)
        self.assertIn('0 <span>/ 109</span>',text)
        self.assertNotIn('Maquette · données fictives',text)

    def test_removed_tagline_does_not_reappear_on_dashboard(self):
        text=render_dashboard(read_history())
        self.assertNotIn("L'atelier des autodidactes",text)
        self.assertIn('MOULINETTE</b>',text)

    def test_persistence_and_latest_per_exercise(self):
        store_attempt(report(),'/some/path/ft_putchar')
        store_attempt(report('c00/ex01'),'/some/path/alphabet')
        store_attempt(report('c00/ex00','failed',[{'name':'Test','status':'fail','message':'bad'}]),'/some/path/fixed')
        data=read_history(); self.assertEqual(data['count'],3)
        self.assertEqual([x['exercise'] for x in data['recent']],['c00/ex00','c00/ex01','c00/ex00'])
        self.assertEqual({x['exercise']:x['result'] for x in data['latest']},{'c00/ex00':'failed','c00/ex01':'passed'})
        self.assertEqual(data['recent'][0]['source_label'],'fixed')
        text=render_dashboard(data)
        self.assertIn('1 <span>/ 109</span>',text)
        self.assertIn('À revoir',text); self.assertIn('Réussi',text)
        self.assertNotIn('/some/path/',text)

    def test_local_score_definition_and_incomplete(self):
        checks=[{'status':'pass'},{'status':'pass'},{'status':'fail'},{'status':'info'}]
        self.assertEqual(score({'checks':checks,'result':'failed'}),67)
        self.assertIsNone(score({'checks':checks+[{'status':'unavailable'}],'result':'failed'}))
        self.assertIsNone(score({'checks':checks,'result':'incomplete'}))
        self.assertIsNone(score({'checks':[{'status':'info'}],'result':'passed'}))

    def test_diagnostics_and_filename_are_html_escaped(self):
        payload='<img src=x onerror="alert(1)">'
        store_attempt(report(checks=[{'name':payload,'status':'fail','message':payload}]),'/rendu/'+payload)
        html=render_dashboard(read_history())
        self.assertNotIn(payload,html); self.assertIn('&lt;img src=x',html)
        self.assertNotIn('https://',html)
        self.assertIn('[hidden]{display:none!important}',html)
        self.assertIn('data:font/woff2;base64,',html)
        self.assertIn('data:application/pdf;base64,',html)

    def test_bad_history_does_not_overwrite_existing_page(self):
        dest=write_dashboard(); before=dest.read_bytes()
        from contextlib import closing
        with closing(sqlite3.connect(data_directory()/'history.sqlite3')) as db, db:
            db.execute("INSERT INTO attempts (created_at,exercise,source_label,result,isolation,checks_json) VALUES ('2026','c00/ex00','x','passed','x','{')")
        with self.assertRaises(HistoryError): write_dashboard()
        self.assertEqual(dest.read_bytes(),before)

    def test_database_symlink_is_rejected(self):
        directory=data_directory();directory.mkdir(mode=0o700,parents=True)
        target=Path(self.tmp.name)/'victim';target.write_text('original')
        (directory/'history.sqlite3').symlink_to(target)
        with self.assertRaises(HistoryError): read_history()
        self.assertEqual(target.read_text(),'original')

    def test_history_does_not_change_json_or_exit_code(self):
        output=io.StringIO(); diagnostic=io.StringIO()
        with patch('moulinette.cli.check_ex00',return_value=report()), contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic):
            code=cli.main(['check','/trusted/ex00','--exercise','c00/ex00','--unsafe-local','--json'])
        self.assertEqual(code,0); self.assertEqual(json.loads(output.getvalue())['result'],'passed')
        self.assertEqual(read_history()['count'],1); self.assertEqual(diagnostic.getvalue(),'')

    def test_history_failure_does_not_change_correction_verdict_or_json(self):
        output=io.StringIO(); diagnostic=io.StringIO()
        with patch('moulinette.cli.check_ex00',return_value=report()), patch('moulinette.cli.store_attempt',side_effect=HistoryError('stockage indisponible')), contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic):
            code=cli.main(['check','/trusted/ex00','--exercise','c00/ex00','--unsafe-local','--json'])
        self.assertEqual(code,0); self.assertEqual(json.loads(output.getvalue())['result'],'passed')
        self.assertIn('Historique non enregistré',diagnostic.getvalue())

    def test_opt_out_does_not_create_history(self):
        with patch('moulinette.cli.check_ex00',return_value=report()), contextlib.redirect_stdout(io.StringIO()):
            code=cli.main(['check','/trusted/ex00','--exercise','c00/ex00','--unsafe-local','--no-history'])
        self.assertEqual(code,0);self.assertFalse(data_directory().exists())

    def test_browser_opens_local_generated_page(self):
        with patch('webbrowser.open',return_value=True) as browser, contextlib.redirect_stdout(io.StringIO()):
            code=cli.main(['dashboard'])
        self.assertEqual(code,0); self.assertTrue(browser.call_args.args[0].startswith('file://'))
        self.assertTrue((data_directory()/'dashboard.html').exists())

    def test_rejects_invalid_records_without_creating_database(self):
        with self.assertRaises(HistoryError): store_attempt({'exercise':'evil','result':'passed','checks':[]},'x')
        self.assertFalse(data_directory().exists())

    def test_history_cap_and_all_latest(self):
        for n in range(53): store_attempt(report('c00/ex0'+str(n%9)),'/trusted/'+str(n))
        data=read_history();self.assertEqual(data['count'],53);self.assertEqual(len(data['recent']),50);self.assertEqual(len(data['latest']),9)

    def test_concurrent_writes_are_not_lost(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda n: store_attempt(report('c00/ex0'+str(n%9)), '/trusted/'+str(n)), range(20)))
        self.assertEqual(read_history()['count'],20)

    def test_browser_unavailable_still_keeps_dashboard_file(self):
        output=io.StringIO(); diagnostic=io.StringIO()
        with patch('webbrowser.open',return_value=False), contextlib.redirect_stdout(output), contextlib.redirect_stderr(diagnostic):
            code=cli.main(['dashboard'])
        self.assertEqual(code,0)
        self.assertTrue((data_directory()/'dashboard.html').exists())
        self.assertIn('Navigateur non ouvert',diagnostic.getvalue())

    def test_custom_relative_xdg_is_ignored(self):
        with patch.dict(os.environ,{'XDG_DATA_HOME':'relative'},clear=False), patch('moulinette.history.Path.home',return_value=Path(self.tmp.name)):
            self.assertEqual(data_directory(),Path(self.tmp.name)/'.local'/'share'/'moulinette-lab')


@unittest.skipUnless(__import__('shutil').which('bwrap') and __import__('shutil').which('cc') and __import__('shutil').which('nm') and __import__('shutil').which('norminette'), 'bwrap, cc, nm et norminette requis')
class DashboardRealIntegrationTests(unittest.TestCase):
    def test_trusted_example_records_real_bwrap_result_and_renders(self):
        import subprocess
        from moulinette.sandbox_doctor import diagnose
        norm=Path(__import__('shutil').which('norminette')).resolve()
        version=subprocess.run([str(norm),'--version'],capture_output=True,text=True,timeout=10)
        if 'norminette 3.3.59' not in (version.stdout+version.stderr).lower() or not (norm.parent.parent/'pyvenv.cfg').is_file(): raise unittest.SkipTest('Norminette 3.3.59 en venv requise')
        checks=[x for x in diagnose()['checks'] if x['name']!='Limites et protection']
        if not checks or any(x['status']!='pass' for x in checks): raise unittest.SkipTest('Bubblewrap indisponible')
        root=Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'XDG_DATA_HOME':tmp}), contextlib.redirect_stdout(io.StringIO()):
            code=cli.main(['check',str(root/'exemples'/'ft_putchar'),'--exercise','c00/ex00','--experimental-sandbox','--json'])
            self.assertEqual(code,0)
            self.assertEqual(read_history()['count'],1)
            self.assertEqual(cli.main(['dashboard','--no-open']),0)
            page=(Path(tmp)/'moulinette-lab'/'dashboard.html').read_text()
            self.assertIn('1 <span>/ 109</span>',page)
            self.assertIn('ft_putchar',page); self.assertIn('Norminette adaptée',page)


    def test_new_project_and_list_results_appear_in_dashboard(self):
        from moulinette.history import read_history
        root=Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'XDG_DATA_HOME':tmp}), contextlib.redirect_stdout(io.StringIO()):
            for ident in ('c10/ex02','c12/ex08'):
                code=cli.main(['check',str(root/'exemples'/ident),'--exercise',ident,'--experimental-sandbox','--json'])
                self.assertEqual(code,0,ident)
            self.assertEqual(read_history()['count'],2)
            self.assertEqual(cli.main(['dashboard','--no-open']),0)
            page=(Path(tmp)/'moulinette-lab'/'dashboard.html').read_text()
            self.assertIn('2 <span>/ 109</span>',page)
            self.assertIn('c10/ex02',page);self.assertIn('c12/ex08',page)


if __name__=='__main__': unittest.main()

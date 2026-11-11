"""Régressions ciblées : fichiers fictifs uniquement, sans test de charge."""
import copy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moulinette.project_engine import ProjectUnavailable, _isolated_norm, _norm_command, evaluate_project
from test_project_engine import MAKE, MAKEFILES


class NormMountValidationTests(unittest.TestCase):
    def test_dedicated_accepted_broad_and_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); home=root/'users'/'alice'; home.mkdir(parents=True)
            broad=home.parent; (broad/'bin').mkdir(); (broad/'bin/norminette').write_text('')
            (broad/'bin/python').write_text(''); (broad/'pyvenv.cfg').write_text('home=fake')
            dedicated=root/'dedicated'; (dedicated/'bin').mkdir(parents=True)
            (dedicated/'bin/norminette').write_text(''); (dedicated/'bin/python').write_text('')
            (dedicated/'pyvenv.cfg').write_text('home=fake')
            with patch('moulinette.project_engine.Path.home',return_value=home):
                with patch('moulinette.project_engine.shutil.which',return_value=str(broad/'bin/norminette')):
                    with self.assertRaises(ProjectUnavailable): _norm_command(True)
                with patch('moulinette.project_engine.shutil.which',return_value=str(dedicated/'bin/norminette')):
                    self.assertEqual(_norm_command(True)[1],dedicated)
                    (dedicated/'pyvenv.cfg').unlink(); (dedicated/'pyvenv.cfg').symlink_to(broad/'pyvenv.cfg')
                    with self.assertRaises(ProjectUnavailable): _norm_command(True)

    def test_other_norm_version_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch('moulinette.project_engine.run_bounded',return_value=(0,b'norminette 3.3.590',b'',False)):
            result=_isolated_norm(Path(tmp),{'style_files':['test.c']},False,['python'],Path(tmp))
        self.assertIn('error',result[0])



@unittest.skipUnless(all(shutil.which(x) for x in ('bwrap','norminette','cc','nm','make')), 'outils requis')
class RealSentinelTest(unittest.TestCase):
    def test_old_mount_exposes_sentinel_new_project_does_not(self):
        # Le témoin ne contient aucune donnée réelle ; on reconstruit le montage
        # antérieur dans un bac éphémère puis on vérifie le parcours actuel.
        found=Path(shutil.which('norminette')).resolve(); source=found.parent.parent
        if not (source/'pyvenv.cfg').is_file(): self.skipTest('venv Norminette requis')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); venv=root/'venv';shutil.copytree(source,venv,symlinks=True)
            (venv/'temoin-fictif').write_text('TEMOIN_FICTIF_UNIQUEMENT')
            bwrap=shutil.which('bwrap')
            cmd=[bwrap,'--unshare-all','--die-with-parent','--ro-bind','/usr','/usr',
                 '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib']
            if Path('/usr/lib64').exists():cmd+=['--symlink','usr/lib64','/lib64']
            cmd+=['--dir','/opt','--ro-bind',str(venv),'/opt/norminette','--',
                  '/usr/bin/cat','/opt/norminette/temoin-fictif']
            old=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
            self.assertEqual(old.returncode,0,old.stderr)
            self.assertEqual(old.stdout,b'TEMOIN_FICTIF_UNIQUEMENT')
            inp=root/'submission';inp.mkdir()
            for name,text in MAKEFILES.items(): (inp/name).write_text(text)
            mk=inp/'Makefile';mk.write_text(mk.read_text().replace('all: demo','all: probe demo\n\nprobe:\n\t@if test -r /opt/norminette/temoin-fictif; then exit 23; fi'))
            norm=(['/opt/norminette/bin/python','-I','-B','-m','norminette'],venv)
            with patch('moulinette.project_engine._norm_command',return_value=norm):
                report=evaluate_project(inp,'t00/ex00',copy.deepcopy(MAKE),sandbox=True)
            self.assertEqual(report['result'],'passed',report)
            self.assertTrue(any(c['name']=='Compilation' and c['status']=='pass' for c in report['checks']),report)
            self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in report['checks']),report)

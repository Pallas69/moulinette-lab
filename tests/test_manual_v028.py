"""Le manuel livré et celui téléchargé sont le même PDF statique."""
import base64
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from moulinette.dashboard import render_dashboard

ROOT=Path(__file__).resolve().parents[1]

class ManualTests(unittest.TestCase):
 def test_pdf_embedded_is_exactly_the_document(self):
  page=render_dashboard({'count':0,'recent':[],'latest':[]})
  for theme in ('ocean','blanc'):
   with self.subTest(theme=theme):
    pattern=rf'data-document="guide-utilisation" data-theme="{theme}" href="data:application/pdf;base64,([^"]+)" download="([^"]+)"'
    match=re.search(pattern,page);self.assertIsNotNone(match)
    pdf=base64.b64decode(match.group(1),validate=True)
    self.assertEqual(pdf,(ROOT/'docs'/('manuel-utilisateur-v0.32.8-'+theme+'.pdf')).read_bytes())
    self.assertEqual(match.group(2),'manuel-moulinette-lab-v0.32.8-'+theme+'.pdf')
  self.assertIn('Manuel utilisateur',page)
 def test_requested_fonts_are_embedded(self):
  pdf=(ROOT/'docs'/'manuel-utilisateur-v0.32.8.pdf').read_bytes()
  self.assertIn(b'LiberationSerif',pdf)
  self.assertIn(b'JetBrainsMono',pdf)
  self.assertIn(b'/FontFile2',pdf)
 def test_editable_source_covers_commands_and_modes(self):
  text=(ROOT/'docs'/'manuel-utilisateur.md').read_text(encoding='utf-8')
  for term in ('--exercise','--module','--all','--watch','--sanitize',
               '--experimental-sandbox','--experimental-cgroup-sandbox',
               '--unsafe-local','--no-history','--json','--trust-github','--ref','--subdir',
               'dashboard --no-open','dashboard --live','sandbox doctor','sandbox selftest','sandbox cgroup-selftest',
               'Norminette 3.3.59','109','non officiel','code de confiance'):
   with self.subTest(term=term):self.assertIn(term,text)
 def test_documented_options_match_cli_help(self):
  p=subprocess.run([sys.executable,'-m','moulinette','check','--help'],cwd=ROOT,
                   capture_output=True,text=True,timeout=10,check=True)
  for option in ('--exercise','--module','--all','--watch','--sanitize',
                 '--experimental-sandbox','--experimental-cgroup-sandbox',
                 '--unsafe-local','--json','--no-history','--trust-github','--ref','--subdir'):
   with self.subTest(option=option):self.assertIn(option,p.stdout)

if __name__=='__main__':unittest.main()

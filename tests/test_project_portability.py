"""Régressions C11/C23 et compilateur durci, sans test de charge."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from moulinette import project_job
from moulinette.exercise_catalog import EXERCISES

ROOT=Path(__file__).resolve().parents[1]/'exemples'
CANARY={'__stack_chk_fail','__stack_chk_guard'}

@unittest.skipUnless(all(shutil.which(x) for x in ('cc','nm','make','ar')),'outils requis')
class PortabilityTests(unittest.TestCase):
 def run_job(self,ident,harden=False,default_c23=False,transform=None):
  cfg=copy.deepcopy(EXERCISES[ident]['project'])
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);inp=base/'in';work=base/'work';shutil.copytree(ROOT/ident,inp)
   if transform:transform(inp)
   names=[p.relative_to(inp).as_posix() for p in inp.rglob('*') if p.is_file()]
   if cfg.get('style_all_sources'):
    cfg['style_files']=[n for n in names if n.endswith(('.c','.h'))]
   if cfg.get('build')=='auto_program':
    cfg['build']='make' if 'Makefile' in names else 'cc'
    if cfg['build']=='cc':cfg['sources']=[n for n in names if n.endswith('.c')];cfg['link_program']=True
   if cfg.get('harness') is not None:cfg['harness']=cfg['harness'].replace('MARKER_BYTES','11, 12, 13')
   cases=[]
   for c in cfg['cases']:
    c=dict(c);e=c['expected']
    if c.pop('marker',False):e+=bytes([11,12,13])
    c['expected']=e.hex()
    for key in ('stdin','expected_stderr'):
     if isinstance(c.get(key),bytes):c[key]=c[key].hex()
    c['fixtures']={k:v.hex() if isinstance(v,bytes) else v for k,v in c.get('fixtures',{}).items()}
    cases.append(c)
   cfg['cases']=cases;cfg['norm_cmd']=None
   spec=base/'cfg.json';spec.write_text(json.dumps(cfg))
   real=project_job.execute;calls=[]
   def execute(cmd,*args,**kw):
    cmd=list(cmd)
    if cmd and cmd[0]=='cc':
     if default_c23:cmd.insert(1,'-std=c2x')
     if harden and '-fno-builtin' in cmd and '-fno-stack-protector' not in cmd:cmd.insert(1,'-fstack-protector-all')
    calls.append(cmd)
    return real(cmd,*args,**kw)
   with patch.object(sys,'argv',['job',str(inp),str(work),str(spec)]),patch.object(project_job,'execute',side_effect=execute):
    result=project_job.main()
   return result,calls
 def test_six_legacy_callback_prototypes_with_c23_default(self):
  for n in (10,11,12,14,16,17):
   ident=f'c12/ex{n:02}'
   with self.subTest(exercise=ident):
    r,calls=self.run_job(ident,default_c23=True)
    self.assertFalse([c for c in r['checks'] if c['status'] in ('fail','unavailable')],r)
    self.assertTrue(any(c['name']=='Adaptation compilation' and 'C11' in c['message'] for c in r['checks']),r)
    compiles=[c for c in calls if '-fno-builtin' in c and '-c' in c]
    self.assertTrue(compiles and all(c.index('-std=c2x')<c.index('-std=c11') for c in compiles),calls)
 def test_hardened_multifile_links_exact_reanalysed_objects(self):
  for ident in ('c08/ex05','c11/ex05','c13/ex07'):
   with self.subTest(exercise=ident):
    r,calls=self.run_job(ident,harden=True)
    self.assertFalse([c for c in r['checks'] if c['status'] in ('fail','unavailable')],r)
    self.assertTrue(any(c['name']=='Adaptation compilation' and '-fno-stack-protector' in c['message'] for c in r['checks']),r)
    alt=[c[c.index('-o')+1] for c in calls if '-fno-stack-protector' in c and '-c' in c]
    self.assertTrue(alt,calls)
    for obj in alt:
     self.assertTrue(any('-u' in c and obj in c for c in calls),calls)
     self.assertTrue(any(c[0]=='cc' and obj in c and '-o' in c and '-c' not in c for c in calls),calls)
 def test_hardened_makefile_executes_original_program_analysis_indicative(self):
  def harden_make(p):
   mk=p/'Makefile';mk.write_text(mk.read_text().replace('CFLAGS = ', 'CFLAGS = -fstack-protector-all '))
  for ident in ('c10/ex00','c10/ex01','c10/ex02','c10/ex03'):
   with self.subTest(exercise=ident):
    r,calls=self.run_job(ident,transform=harden_make)
    self.assertFalse([c for c in r['checks'] if c['status'] in ('fail','unavailable')],r)
    note=next(c['message'] for c in r['checks'] if c['name']=='Adaptation compilation')
    self.assertIn('indicative',note);self.assertIn('ne sont pas ceux liés',note)
    self.assertTrue(any('-fno-stack-protector' in c for c in calls))
    self.assertTrue(any(c['name'].startswith('Test ') and c['status']=='pass' for c in r['checks']))
 def test_simultaneous_forbidden_external_and_canary_fail(self):
  def inject(p):
   f=p/'helpers.c';s=f.read_text();s='#include <stdio.h>\n'+s
   s=s.replace('void\tft_text(char *s)\n{','void\tft_text(char *s)\n{\n\tputs("forbidden");');f.write_text(s)
  r,calls=self.run_job('c11/ex05',harden=True,transform=inject)
  self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='fail' and 'puts' in c['message'] for c in r['checks']),r)
  self.assertFalse(any(c['name'].startswith('Test ') for c in r['checks']))
 def test_forbidden_external_in_alternate_fails_before_link(self):
  def inject(p):
   f=p/'helpers.c';s=f.read_text();s='#ifndef __SSP_ALL__\n#include <stdio.h>\n#endif\n'+s
   s=s.replace('void\tft_text(char *s)\n{','void\tft_text(char *s)\n{\n#ifndef __SSP_ALL__\n\tputs("forbidden");\n#endif');f.write_text(s)
  r,calls=self.run_job('c11/ex05',harden=True,transform=inject)
  self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='fail' and 'puts' in c['message'] for c in r['checks']),r)
  self.assertFalse(any(c['name'].startswith('Test ') for c in r['checks']))
  self.assertFalse(any(c[0]=='cc' and '-o' in c and '-c' not in c for c in calls),calls)
 def test_makefile_forbidden_calls_in_original_and_alternate(self):
  for alternate_only in (False,True):
   with self.subTest(alternate_only=alternate_only):
    def inject(p):
     mk=p/'Makefile';mk.write_text(mk.read_text().replace('CFLAGS = ','CFLAGS = -fstack-protector-all '))
     f=p/'main.c';src=f.read_text()
     if alternate_only:
      src='#ifndef __SSP_ALL__\n#include <stdio.h>\n#endif\n'+src
      extra='#ifndef __SSP_ALL__\n\tputs("bad");\n#endif\n'
     else:
      src='#include <stdio.h>\n'+src;extra='\tputs("bad");\n'
     src=src.replace('int\tmain(int argc, char **argv)\n{','int\tmain(int argc, char **argv)\n{\n'+extra);f.write_text(src)
    r,calls=self.run_job('c10/ex00',transform=inject)
    self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='fail' and 'puts' in c['message'] for c in r['checks']),r)
    self.assertFalse(any(c['name'].startswith('Test ') for c in r['checks']))
    if alternate_only:self.assertTrue(any('-fno-stack-protector' in c for c in calls),calls)
    else:self.assertFalse(any('-fno-stack-protector' in c for c in calls),calls)
 def test_explicit_stack_symbol_remains_incomplete(self):
  def inject(p):
   f=p/'helpers.c';s=f.read_text();s='extern void __stack_chk_fail(void);\n'+s
   s=s.replace('void\tft_text(char *s)\n{','void\tft_text(char *s)\n{\n\tif (*s == 42) __stack_chk_fail();');f.write_text(s)
  r,calls=self.run_job('c11/ex05',harden=True,transform=inject)
  self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='unavailable' and '__stack_chk_fail' in c['message'] for c in r['checks']),r)
  self.assertFalse(any(c['name'].startswith('Test ') for c in r['checks']))

@unittest.skipUnless(all(shutil.which(x) for x in ('cc','gcc','nm','make','bwrap','norminette','ar')),'outils requis')
class RealBubblewrapPortabilityTests(unittest.TestCase):
 def test_13_reported_exercises_with_c23_and_hardening_defaults(self):
  from moulinette import project_engine
  from moulinette.checker import check_exercise
  from moulinette.cgroup_launcher import _validate_favorable_checks
  ids=['c08/ex05',*(f'c10/ex{i:02}' for i in range(4)),'c11/ex05',
       *(f'c12/ex{i:02}' for i in (10,11,12,14,16,17)),'c13/ex07']
  real=project_engine.run_bounded
  with tempfile.TemporaryDirectory() as t:
   wrapper=Path(t)/'cc'
   wrapper.write_text('#!/bin/sh\nexec /usr/bin/gcc -std=c2x -fstack-protector-all "$@"\n')
   wrapper.chmod(0o755)
   def run(command,*args,**kwargs):
    command=list(command)
    if '--chdir' in command:
     pos=command.index('--chdir')
     command[pos:pos]=['--dir','/opt/fakebin','--ro-bind',str(wrapper),'/opt/fakebin/cc']
     for i in range(len(command)-2):
      if command[i:i+2]==['--setenv','PATH']:
       command[i+2]='/opt/fakebin:/usr/bin:/bin';break
    return real(command,*args,**kwargs)
   with patch('moulinette.project_engine.run_bounded',side_effect=run):
    for ident in ids:
     with self.subTest(exercise=ident):
      r=check_exercise(ROOT/ident,ident,sandbox=True)
      self.assertEqual(r['result'],'passed',r)
      self.assertTrue(any(c['name']=='Adaptation compilation' and 'stack-protector' in c['message'] for c in r['checks']),r)
      self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in r['checks']),r)
      _validate_favorable_checks(ident,r['checks'])

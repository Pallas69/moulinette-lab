"""Premiers essais du moteur de projets : code de confiance uniquement."""
import shutil
import tempfile
import unittest
from pathlib import Path
from moulinette.project_engine import evaluate_project
from moulinette.cgroup_launcher import _validate_favorable_checks
from unittest.mock import patch

BASE={'subject_version':'1','project':{
 'required_files':['ft_add.c','ft_twice.c','ft_project.h'],'exact_files':True,
 'sources':['ft_add.c','ft_twice.c'],'build':'cc','binary':'test-projet',
 'allowed_functions':[],'support_functions':[],
 'prototype':'#include "ft_project.h"\n_Static_assert(_Generic(&ft_add, int (*)(int, int): 1, default: 0), "ft_add");\n',
 'harness':'#include <unistd.h>\n#include "ft_project.h"\nstatic const unsigned char m[]={MARKER_BYTES};\nint main(void){if(ft_twice(ft_add(2,3))!=10)return 1;write(1,"OK",2);write(1,m,sizeof m);return 73;}\n',
 'cases':[{'label':'addition et deux fichiers','expected':b'OK','marker':True,'code':73}],
 'style_files':['ft_add.c','ft_twice.c','ft_project.h'],
}}
FILES={
 'ft_project.h':'#ifndef FT_PROJECT_H\n# define FT_PROJECT_H\n\nint\tft_add(int a, int b);\nint\tft_twice(int a);\n\n#endif\n',
 'ft_add.c':'#include "ft_project.h"\n\nint\tft_add(int a, int b)\n{\n\treturn (a + b);\n}\n',
 'ft_twice.c':'#include "ft_project.h"\n\nint\tft_twice(int a)\n{\n\treturn (ft_add(a, a));\n}\n',
}
MAKE={'subject_version':'1','project':{
 'required_files':['Makefile','main.c'],'exact_files':True,'sources':['main.c'],'build':'make','binary':'demo',
 'allowed_functions':['write'],'cases':[{'label':'programme','argv':['hello'],'expected':b'hello\n','code':0}],
 'style_files':['main.c'],
}}
MAKEFILES={'Makefile':'all: demo\n\ndemo: main.o\n\tcc main.o -o demo\n\nmain.o: main.c\n\tcc -Wall -Wextra -Werror -c main.c -o main.o\n',
 'main.c':'#include <unistd.h>\n\nint\tmain(int argc, char **argv)\n{\n\tint\ti;\n\n\tif (argc != 2)\n\t\treturn (1);\n\ti = 0;\n\twhile (argv[1][i])\n\t\ti++;\n\twrite(1, argv[1], i);\n\twrite(1, "\\n", 1);\n\treturn (0);\n}\n'}

@unittest.skipUnless(shutil.which('bwrap') and shutil.which('cc') and shutil.which('nm') and shutil.which('norminette') and shutil.which('make'),'outils requis')
class ProjectEngineTest(unittest.TestCase):
 def run_sample(self,spec,files,sandbox=True):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for name,contents in files.items():
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(contents)
   before={n:(root/n).read_bytes() for n in files}
   report=evaluate_project(root,'t00/ex00',spec,sandbox=sandbox)
   self.assertEqual(before,{n:(root/n).read_bytes() for n in files})
   self.assertEqual(set(root.rglob('*')),{root/n for n in files}|{(root/n).parent for n in files if (root/n).parent!=root})
   return report
 def test_multi_c_and_header_with_norm_and_real_bwrap(self):
  r=self.run_sample(BASE,FILES);self.assertEqual(r['result'],'passed',r)
  self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='pass' for c in r['checks']))
 def test_make_program_with_norm_and_real_bwrap(self):
  r=self.run_sample(MAKE,MAKEFILES);self.assertEqual(r['result'],'passed',r)
 def test_wrong_implementation_fails(self):
  files=dict(FILES,**{'ft_twice.c':FILES['ft_twice.c'].replace('ft_add(a, a)','ft_add(a, 1)')})
  r=self.run_sample(BASE,files);self.assertEqual(r['result'],'failed',r)
  self.assertTrue(any(c['name']=='Test addition et deux fichiers' and c['status']=='fail' for c in r['checks']))
 def test_extra_file_and_missing_required_file(self):
  r=self.run_sample(BASE,dict(FILES,extra='x'));self.assertEqual(r['result'],'failed',r)
  r=self.run_sample(BASE,{k:v for k,v in FILES.items() if k!='ft_project.h'});self.assertEqual(r['result'],'failed',r)
 def test_make_rules_with_provided_files_and_no_norm_on_makefile(self):
  spec={'subject_version':'1','project':{'required_files':['Makefile'],'exact_files':True,
   'provided_files':{'main.c':MAKEFILES['main.c']},'sources':[],'build':'make','binary':'demo',
   'skip_external_inspection':True,'style_files':[],
   'cases':[{'label':'à jour','runner':'make','argv':['-q'],'expected':b'','code':0},
            {'label':'clean','runner':'make','argv':['clean'],'expected':b'','ignore_stdout':True,'must_absent':['main.o']},
            {'label':'fclean','runner':'make','argv':['fclean'],'expected':b'','ignore_stdout':True,'must_absent':['main.o','demo']},
            {'label':'re','runner':'make','argv':['re'],'expected':b'','ignore_stdout':True,'must_exist':['main.o','demo']}]}}
  mk=MAKEFILES['Makefile']+'\nclean:\n\trm -f main.o\n\nfclean: clean\n\trm -f demo\n\nre: fclean all\n'
  r=self.run_sample(spec,{'Makefile':mk});self.assertEqual(r['result'],'passed',r)
  self.assertTrue(any(c['name']=='Norminette adaptée' and c['status']=='info' for c in r['checks']),r)
 def test_script_archives_objects_and_links_the_archive(self):
  from copy import deepcopy
  spec=deepcopy(BASE);cfg=spec['project'];cfg.update({
   'required_files':['ft_add.c','ft_twice.c','ft_project.h','lib.sh'],
   'build':'script','script':'lib.sh','inspect_archives':['libdemo.a'],'link_inputs':['libdemo.a']})
  files=dict(FILES,**{'lib.sh':'cc -Wall -Wextra -Werror -c ft_add.c ft_twice.c\nar rc libdemo.a ft_add.o ft_twice.o\nrm ft_add.o ft_twice.o\n'})
  r=self.run_sample(spec,files);self.assertEqual(r['result'],'passed',r)
 def test_external_function_restriction_is_enforced_on_all_objects(self):
  files=dict(FILES,**{'ft_add.c':'#include "ft_project.h"\n#include <stdio.h>\nint ft_add(int a, int b) { puts("extra"); return a+b; }\n'})
  r=self.run_sample(BASE,files);self.assertEqual(r['result'],'failed',r)
  self.assertTrue(any(c['name']=='Fonctions externes' and c['status']=='fail' for c in r['checks']),r)
 def test_header_only_and_checkdefine(self):
  spec={'subject_version':'1','project':{'required_files':['ft_abs.h'],'exact_files':True,
   'sources':[],'build':'cc','require_objects':False,'binary':'test-header','allowed_functions':[],
   'harness':'#include "ft_abs.h"\nint main(void){return ABS(-4)!=4 || ABS(7)!=7 || ABS(0)!=0;}\n',
   'cases':[{'label':'macro ABS','expected':b'', 'code':0}],
   'style_files':['ft_abs.h'],'checkdefine':['ft_abs.h']}}
  files={'ft_abs.h':'#ifndef FT_ABS_H\n# define FT_ABS_H\n\n# define ABS(Value) (((Value) < 0) * -(Value) + ((Value) >= 0) * (Value))\n\n#endif\n'}
  r=self.run_sample(spec,files);self.assertEqual(r['result'],'passed',r)

 def test_unsafe_local_with_suitable_environment(self):
  r=self.run_sample(BASE,FILES,sandbox=False);self.assertEqual(r['result'],'passed',r)

class ProjectGithubProtocolTest(unittest.TestCase):
 def sample(self):
  import base64
  return {'version':2,'files':[{'path':'src/main.c','data_b64':base64.b64encode(b'int main(void){return 0;}').decode()}],
          'dirs':['src'],'source':{'kind':'github','url':'https://github.com/a/b','commit':'a'*40,'ref':'HEAD','subdir':'.'}}
 def test_valid_project_and_reconstruction(self):
  from moulinette.github_bounded import _parse_project_snapshot,bounded_public_repository
  from moulinette.exercise_catalog import EXERCISES
  payload=self.sample();parsed=_parse_project_snapshot(payload,'https://github.com/a/b','HEAD','.')
  self.assertIn('src/main.c',parsed['files'])
  spec={'source':'Makefile','project':{},'cases':[]}
  with patch.dict(EXERCISES,{'t00/ex00':spec}),patch('moulinette.github_bounded._fetch_snapshot',return_value=payload):
   with bounded_public_repository('https://github.com/a/b','t00/ex00') as (p,source):
    self.assertEqual((p/'src/main.c').read_bytes(),b'int main(void){return 0;}')
    self.assertEqual(source['commit'],'a'*40)
 def test_rejects_traversal_inconsistent_tree_and_bad_provenance(self):
  from moulinette.github_bounded import _parse_project_snapshot
  from moulinette.github_source import GitHubSourceError
  for mutate in ('traversal','missing-parent','forged-commit','duplicate'):
   payload=self.sample()
   if mutate=='traversal':payload['files'][0]['path']='../escape'
   elif mutate=='missing-parent':payload['dirs']=[]
   elif mutate=='forged-commit':payload['source']['url']='https://github.com/other/repo'
   else:payload['files'].append(payload['files'][0])
   with self.subTest(mutate=mutate),self.assertRaises(GitHubSourceError):
    _parse_project_snapshot(payload,'https://github.com/a/b','HEAD','.')

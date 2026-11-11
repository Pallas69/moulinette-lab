"""C 11 v8.0 : programme do-op avec fichiers libres."""
from .project_catalog import project_spec
_cases=[
 {'label':'sans arguments','argv':[],'expected':b'','expected_stderr':b''},
 {'label':'addition','argv':['42','+','21'],'expected':b'63\n','expected_stderr':b''},
 {'label':'soustraction et signes','argv':['42amis','-','--+-20toto12'],'expected':b'62\n','expected_stderr':b''},
 {'label':'multiplication','argv':['-7','*','3'],'expected':b'-21\n','expected_stderr':b''},
 {'label':'division signée','argv':['-11','/','3'],'expected':b'-3\n','expected_stderr':b''},
 {'label':'modulo signé','argv':['-11','%','3'],'expected':b'-2\n','expected_stderr':b''},
 {'label':'opérateur invalide','argv':['1','p','1'],'expected':b'0\n','expected_stderr':b''},
 {'label':'division par zéro','argv':['25','/','0'],'expected':b'Stop : division by zero\n','expected_stderr':b''},
 {'label':'modulo par zéro','argv':['25','%','0'],'expected':b'Stop : modulo by zero\n','expected_stderr':b''},
 {'label':'conversions partielles','argv':['1','+','toto3'],'expected':b'1\n','expected_stderr':b''},
 {'label':'trop peu d’arguments','argv':['1','+'],'expected':b'','expected_stderr':b''},
 {'label':'trop d’arguments','argv':['1','+','1','extra'],'expected':b'','expected_stderr':b''},
 {'label':'opérateur en mot','argv':['foo','plus','bar'],'expected':b'0\n','expected_stderr':b''},
 {'label':'opérateur avec caractères supplémentaires','argv':['1','++','1'],'expected':b'0\n','expected_stderr':b''},
 {'label':'conversion du premier opérande','argv':['toto3','+','4'],'expected':b'4\n','expected_stderr':b''}]
_cfg={'required_files':[],'exact_files':False,'build':'auto_program','binary':'do-op','allowed_functions':['write'],
      'fallback_inspection':True,'cases':_cases,'style_all_sources':True}
C11_PROJECT_EXERCISES={'c11/ex05':project_spec('do-op','8.0',_cfg)}

"""C 10 v7.1 : programmes Makefile et fichiers de test non officiels."""
from .project_catalog import project_spec

def program_spec(name,cases,allowed):
 cfg={'required_files':['Makefile'],'exact_files':False,'build':'make','binary':name,
      'make_compile_pattern':r'(?m)\bcc\b(?=[^\n]*\s-Wall\b)(?=[^\n]*\s-Wextra\b)(?=[^\n]*\s-Werror\b)',
      'fallback_inspection':True,'allowed_functions':allowed,'cases':cases+[
       {'label':'Makefile clean','runner':'make','argv':['clean'],'expected':b'','ignore_stdout':True,'must_exist':[name]},
       {'label':'Makefile fclean','runner':'make','argv':['fclean'],'expected':b'','ignore_stdout':True,'must_absent':[name]},
       {'label':'Makefile all après nettoyage','runner':'make','argv':['all'],'expected':b'','ignore_stdout':True,'must_exist':[name]}],
      'style_all_sources':True}
 return project_spec('Makefile','7.1',cfg)

_sample=bytes(range(256))*20  # 5 Kio, binaire et plus d'un bloc de lecture courant.
_AL=['close','open','read','write','strerror','basename','__xpg_basename','__errno_location']
_c0=[{'label':'fichier texte','argv':['a.txt'],'fixtures':{'a.txt':b'Bonjour\n42\n'},'expected':b'Bonjour\n42\n','expected_stderr':b''},
 {'label':'fichier binaire','argv':['b.bin'],'fixtures':{'b.bin':b'\x00A\xff\n'},'expected':b'\x00A\xff\n','expected_stderr':b''},
 {'label':'nom manquant','argv':[],'expected':b'','expected_stderr':b'File name missing.\n','codes':[0,1,2]},
 {'label':'trop de noms','argv':['a.txt','b.bin'],'expected':b'','expected_stderr':b'Too many arguments.\n','codes':[0,1,2]},
 {'label':'fichier illisible','argv':['manquant'],'expected':b'','expected_stderr':b'Cannot read file.\n','codes':[0,1,2]}]
_c0.append({'label':'fichier binaire de 5 Kio','argv':['long.bin'],'fixtures':{'long.bin':_sample},'expected':_sample,'expected_stderr':b''})
_c1=[{'label':'tiret stdin entre fichiers','argv':['a','-','b'],'stdin':b'std','fixtures':{'a':b'A','b':b'B'},'expected':b'AstdB','expected_stderr':b''},
 {'label':'entrée standard','argv':[],'stdin':b'abc\n\x00\xff','expected':b'abc\n\x00\xff','expected_stderr':b''},
 {'label':'un fichier','argv':['a'],'fixtures':{'a':b'a1\na2\n'},'expected':b'a1\na2\n','expected_stderr':b''},
 {'label':'concaténation','argv':['a','b'],'fixtures':{'a':b'AB\x00','b':b'\xff\nZ'},'expected':b'AB\x00\xff\nZ','expected_stderr':b''},
 {'label':'fichier vide','argv':['vide'],'fixtures':{'vide':b''},'expected':b'','expected_stderr':b''}]
_c1.append({'label':'cat binaire de 5 Kio','argv':['long.bin'],'fixtures':{'long.bin':_sample},'expected':_sample,'expected_stderr':b''})
_c2=[{'label':'option collee et fichier','argv':['-c3','a'],'fixtures':{'a':b'abcdef'},'expected':b'def','expected_stderr':b''},
 {'label':'option collee et stdin','argv':['-c2'],'stdin':b'abcde','expected':b'de','expected_stderr':b''},
 {'label':'suffixe de fichier','argv':['-c','3','a'],'fixtures':{'a':b'abcdef\n'},'expected':b'ef\n','expected_stderr':b''},
 {'label':'zéro octet','argv':['-c','0','a'],'fixtures':{'a':b'abcdef\n'},'expected':b'','expected_stderr':b''},
 {'label':'taille supérieure','argv':['-c','20','a'],'fixtures':{'a':b'abc\n'},'expected':b'abc\n','expected_stderr':b''},
 {'label':'entrée standard','argv':['-c','4'],'stdin':b'xyz0123\n','expected':b'123\n','expected_stderr':b''},
 {'label':'plusieurs fichiers','argv':['-c','4','a','b'],'fixtures':{'a':b'abcdef\n','b':b'1234567890\n'},'expected':b'==> a <==\ndef\n\n==> b <==\n890\n','expected_stderr':b''}]
_c2.append({'label':'tail binaire sur fichier de 5 Kio','argv':['-c','300','long.bin'],'fixtures':{'long.bin':_sample},'expected':_sample[-300:],'expected_stderr':b''})
_hd_short=b'00000000  61 62 63 0a 00 ff                                 |abc...|\n00000006\n'
_hd_sixteen=b'00000000  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f  |................|\n00000010\n'
_hd_seventeen=b'00000000  30 31 32 33 34 35 36 37  38 39 61 62 63 64 65 66  |0123456789abcdef|\n00000010  21                                                |!|\n00000011\n'
_hd_repeat=b'00000000  41 41 41 41 41 41 41 41  41 41 41 41 41 41 41 41  |AAAAAAAAAAAAAAAA|\n*\n00000030  5a                                                |Z|\n00000031\n'
_c3=[{'label':'deux fichiers concaténés','argv':['-C','a','b'],'fixtures':{'a':b'foo','b':b'bar'},'expected':b'00000000  66 6f 6f 62 61 72                                 |foobar|\n00000006\n','expected_stderr':b''},
 {'label':'entrée vide','argv':['-C'],'stdin':b'','expected':b'','expected_stderr':b''},
 {'label':'octets mixtes','argv':['-C','a'],'fixtures':{'a':b'abc\n\x00\xff'},'expected':_hd_short,'expected_stderr':b''},
 {'label':'ligne complète','argv':['-C','a'],'fixtures':{'a':bytes(range(16))},'expected':_hd_sixteen,'expected_stderr':b''},
 {'label':'seconde ligne','argv':['-C','a'],'fixtures':{'a':b'0123456789abcdef!'},'expected':_hd_seventeen,'expected_stderr':b''},
 {'label':'lignes répétées','argv':['-C','a'],'fixtures':{'a':b'A'*48+b'Z'},'expected':_hd_repeat,'expected_stderr':b''}]
_c3.append({'label':'hexdump entrée standard binaire','argv':['-C'],'stdin':bytes(range(16)),'expected':_hd_sixteen,'expected_stderr':b''})
C10_EXERCISES={
 'c10/ex00':program_spec('ft_display_file',_c0,['close','open','read','write']),
 'c10/ex01':program_spec('ft_cat',_c1,_AL),
 'c10/ex02':program_spec('ft_tail',_c2,_AL+['malloc','free']),
 'c10/ex03':program_spec('ft_hexdump',_c3,_AL+['malloc','free']),
}

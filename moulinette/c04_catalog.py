"""C 04 v5 : tests pédagogiques, sans évaluation des dépassements d'entier."""
from copy import deepcopy
from .c01_catalog import C01_EXERCISES, _spec, _prototype


def spec(*a,**kw):
 s=_spec(*a,**kw);s['subject_version']='5';return s

def build_c04(existing):
 out={}
 for dest,old in [('c04/ex00','c01/ex06'),('c04/ex01','c01/ex05'),('c04/ex02','c00/ex07')]:
  source=C01_EXERCISES if old.startswith('c01') else existing
  out[dest]=deepcopy(source[old]);out[dest]['subject_version']='5'
 # C00/ex07 assumes 32-bit int and tells the harness if unsupported.
 out['c04/ex02']['allowed_functions']={'write'}
 out['c04/ex03']=spec('ft_atoi','int','char *',[
  ('vide','char s[]=""; return ft_atoi(s)==0;'),('espaces et signes du sujet','char s[]=" ---+--+1234ab567"; return ft_atoi(s)==-1234;'),
  ('blancs ASCII','char s[]=" \\t\\n\\v\\f\\r+42!"; return ft_atoi(s)==42;'),('zéros','char s[]="000123"; return ft_atoi(s)==123;'),
  ('signes pairs','char s[]="--+--45"; return ft_atoi(s)==45;'),('signes sans chiffres','char s[]="---x23"; return ft_atoi(s)==0;'),
  ('blanc après signe','char s[]="- 12"; return ft_atoi(s)==0;'),('caractère initial invalide','char s[]="abc42"; return ft_atoi(s)==0;'),
  ('valeur négative','char s[]="-123456"; return ft_atoi(s)==-123456;')])
 lines=[('zéro décimal','0',b'0','ft_putnbr_base(0,"0123456789");'),
 ('entier négatif','1',b'-42','ft_putnbr_base(-42,"0123456789");'),
 ('binaire','2',b'101010','ft_putnbr_base(42,"01");'),
 ('hexadécimal','3',b'2A','ft_putnbr_base(42,"0123456789ABCDEF");'),
 ('base poneyvif','4',b'vif','ft_putnbr_base(375,"poneyvif");'),
 ('base vide','5',b'','ft_putnbr_base(42,"");'),('base de taille un','6',b'','ft_putnbr_base(42,"x");'),
 ('base dupliquée','7',b'','ft_putnbr_base(42,"01230");'),('base avec signe','8',b'','ft_putnbr_base(42,"01+");'),
 ('int minimum','9',str(-(2**31)).encode(),'ft_putnbr_base(INT_MIN,"0123456789");')]
 cases='\n'.join(f"case '{arg}': {call} break;" for _,arg,_,call in lines)
 harness='''#include <limits.h>\n#include <unistd.h>\n#if INT_MAX != 2147483647 || INT_MIN != (-2147483647-1)\n#error ML_INT_PLATFORM_UNSUPPORTED\n#endif\nvoid ft_putnbr_base(int,char *);\nstatic const unsigned char marker[] = { MARKER_BYTES };\nint main(int argc,char **argv) { if(argc!=2)return 2; switch(argv[1][0]) {\n'''+cases+'''\ndefault:return 2; } if(write(1,marker,sizeof marker)!=(ssize_t)sizeof marker)return 74; return 73; }\n'''
 out['c04/ex04']={'source':'ft_putnbr_base.c','executable':'test-ft_putnbr_base','subject_version':'5','allowed_functions':{'write'},'prototype':_prototype('ft_putnbr_base','void','int, char *'),'harness':harness,'cases':[(a,b,c) for a,b,c,_ in lines]}
 out['c04/ex05']=spec('ft_atoi_base','int','char *, char *',[
 ('décimal','char s[]=" ---+--+1234ab567",b[]="0123456789";return ft_atoi_base(s,b)==-1234;'),
 ('binaire','char s[]="+101010",b[]="01";return ft_atoi_base(s,b)==42;'),
 ('hexadécimal','char s[]=" -2A!",b[]="0123456789ABCDEF";return ft_atoi_base(s,b)==-42;'),
 ('base non numérique','char s[]="fif",b[]="poneyvif";return ft_atoi_base(s,b)==(7*64+6*8+7);'),
 ('arrêt au premier caractère invalide','char s[]="1012",b[]="01";return ft_atoi_base(s,b)==5;'),
 ('base vide','char s[]="123",b[]="";return ft_atoi_base(s,b)==0;'),
 ('base un caractère','char s[]="x",b[]="x";return ft_atoi_base(s,b)==0;'),
 ('base dupliquée','char s[]="101",b[]="010";return ft_atoi_base(s,b)==0;'),
 ('base avec signe','char s[]="10",b[]="01-";return ft_atoi_base(s,b)==0;'),
 ('base avec blanc','char s[]="10",b[]="01 ";return ft_atoi_base(s,b)==0;')])
 return out

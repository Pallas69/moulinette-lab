"""C 07/ex04 : conversion avec deux fichiers étudiants."""
from .c01_catalog import _condition_harness, _prototype
from .project_catalog import project_spec
_helpers=r'''
#include <stdlib.h>
#include <string.h>
static int convert_case(char *n,char *from,char *to,const char *expected)
{
 char *p=ft_convert_base(n,from,to);int ok;
 if(!expected)return p==NULL;
 if(!p || p==n || p==from || p==to)return 0;
 ok=strcmp(p,expected)==0;free(p);return ok;
}
'''
_branches=[('décimal vers hexadécimal','return convert_case(" ---+--+1234ab567","0123456789","0123456789abcdef","-4d2");'),
 ('binaire vers décimal','return convert_case("101010","01","0123456789","42");'),
 ('zéro vers base personnalisée','return convert_case("0","01","poneyvif","p");'),
 ('signes multiples','return convert_case("  --+101","01","0123456789","5");'),
 ('arrêt au caractère invalide','return convert_case("1012","01","0123456789","5");'),
 ('aucun chiffre','return convert_case("z","0123456789","01","0");'),
 ('base de départ invalide','return convert_case("1","001","01",NULL);'),
 ('base de destination invalide','return convert_case("1","01","0+",NULL);'),
 ('blanc dans la base','return convert_case("1","01 ","01",NULL);'),
 ('minimum int 32 bits','return convert_case("-80000000","0123456789abcdef","0123456789","-2147483648");')]
_harness=_condition_harness('char *ft_convert_base(char *, char *, char *);',_branches,_helpers)
_files=['ft_convert_base.c','ft_convert_base2.c']
_cfg={'required_files':_files,'exact_files':True,'sources':_files,'build':'cc','binary':'test-convert',
      'allowed_functions':['malloc','free'],'prototype':_prototype('ft_convert_base','char *','char *, char *, char *'),
      'harness':_harness,'cases':[{'label':label,'argv':[str(i)],'expected':b'OK','marker':True,'code':73} for i,(label,_) in enumerate(_branches)],
      'style_files':_files}
C07_PROJECT_EXERCISES={'c07/ex04':project_spec(_files[0],'6',_cfg)}

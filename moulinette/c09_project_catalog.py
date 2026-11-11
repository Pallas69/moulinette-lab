"""C 09 v5.0 : script de bibliothèque et Makefile."""
from .c01_catalog import _condition_harness
from .project_catalog import project_spec

_LIB_C={
'ft_putchar.c':'#include <unistd.h>\nvoid ft_putchar(char c) { write(1,&c,1); }\n',
'ft_swap.c':'void ft_swap(int *a,int *b) {int t=*a;*a=*b;*b=t;}\n',
'ft_putstr.c':'#include <unistd.h>\nvoid ft_putstr(char *s){while(*s)write(1,s++,1);}\n',
'ft_strlen.c':'int ft_strlen(char *s){int i=0;while(s[i])i++;return i;}\n',
'ft_strcmp.c':'int ft_strcmp(char *a,char *b){while(*a && *a==*b){a++;b++;}return (unsigned char)*a-(unsigned char)*b;}\n'}
_decl='''void ft_putchar(char); void ft_swap(int *,int *); void ft_putstr(char *);
int ft_strlen(char *); int ft_strcmp(char *,char *);'''
_branches=[('affichage',"ft_putchar('X'); ft_putstr(\"abc\"); return 1;"),
 ('échange','int a=3,b=-9;ft_swap(&a,&b);return a==-9 && b==3;'),
 ('longueurs','char a[]="",b[]="abc";return ft_strlen(a)==0 && ft_strlen(b)==3;'),
 ('comparaison','char a[]="abc",b[]="abd",c[]="abc";return ft_strcmp(a,b)<0 && ft_strcmp(b,a)>0 && ft_strcmp(a,c)==0;')]
_harness=_condition_harness(_decl,_branches)
_cases=[{'label':l,'argv':[str(i)],'expected':b'XabcOK' if i==0 else b'OK','marker':True,'code':73} for i,(l,_) in enumerate(_branches)]
_files=['libft_creator.sh',*_LIB_C]
_cfg={'required_files':_files,'exact_files':True,'sources':list(_LIB_C),'build':'script','script':'libft_creator.sh','binary':'test-libft',
      'inspect_archives':['libft.a'],'link_inputs':['libft.a'],'allowed_functions':['write'],'harness':_harness,'cases':_cases,
      'style_files':list(_LIB_C)}
C09_PROJECT_EXERCISES={'c09/ex00':project_spec('libft_creator.sh','5.0',_cfg)}

_provided={'srcs/'+name:content for name,content in _LIB_C.items()}
_provided['includes/ft.h']='#ifndef FT_H\n#define FT_H\n'+_decl+'\n#endif\n'
_obj=['srcs/'+n.removesuffix('.c')+'.o' for n in _LIB_C]
_makecases=_cases+[
 {'label':'aucune recompilation nécessaire','runner':'make','argv':['-q'],'expected':b'','code':0,'must_exist':['libft.a',*_obj]},
 {'label':'clean supprime les objets','runner':'make','argv':['clean'],'expected':b'','ignore_stdout':True,'stdout_nonempty':True,'must_absent':_obj,'must_exist':['libft.a']},
 {'label':'fclean supprime aussi la bibliothèque','runner':'make','argv':['fclean'],'expected':b'','ignore_stdout':True,'must_absent':['libft.a',*_obj]},
 {'label':'re reconstruit','runner':'make','argv':['re'],'expected':b'','ignore_stdout':True,'stdout_nonempty':True,'must_exist':['libft.a',*_obj]},
 {'label':'all est à jour','runner':'make','argv':['-q','all'],'expected':b'','code':0},
 {'label':'libft.a est à jour','runner':'make','argv':['-q','libft.a'],'expected':b'','code':0}]
_cfg={'required_files':['Makefile'],'exact_files':True,'provided_files':_provided,'sources':[],'build':'make','binary':'test-libft',
      'inspect_archives':['libft.a'],'link_inputs':['libft.a'],'skip_external_inspection':True,
      'make_compile_pattern':r'(?m)\bcc\b[^\n]*-Wall\s+-Wextra\s+-Werror\b',
      'allowed_functions':[],'harness':_harness,'cases':_makecases,'style_files':[]}
C09_PROJECT_EXERCISES['c09/ex01']=project_spec('Makefile','5.0',_cfg)

"""C 08 v14 : en-têtes et structures. Tests non officiels."""
from .c01_catalog import _condition_harness, _prototype
from .project_catalog import project_spec

C08_EXERCISES={}

def header_spec(filename,harness,cases,define=False):
 cfg={'required_files':[filename],'exact_files':True,'sources':[],'build':'cc',
      'require_objects':False,'binary':'test-header','harness':harness,
      'allowed_functions':[],'cases':cases,'style_files':[filename],
      'checkdefine':[filename] if define else []}
 return project_spec(filename,'14',cfg)

_h=r'''#include "ft.h"
#include "ft.h"
_Static_assert(_Generic(&ft_putchar, void (*)(char):1, default:0), "ft_putchar");
_Static_assert(_Generic(&ft_swap, void (*)(int *, int *):1, default:0), "ft_swap");
_Static_assert(_Generic(&ft_putstr, void (*)(char *):1, default:0), "ft_putstr");
_Static_assert(_Generic(&ft_strlen, int (*)(char *):1, default:0), "ft_strlen");
_Static_assert(_Generic(&ft_strcmp, int (*)(char *, char *):1, default:0), "ft_strcmp");
int main(void) { return 0; }
'''
C08_EXERCISES['c08/ex00']=header_spec('ft.h',_h,[{'label':'prototypes et inclusions répétées','expected':b''}])
_h=r'''#include "ft_boolean.h"
#include "ft_boolean.h"
void ft_putstr(char *str) { while (*str) write(1,str++,1); }
t_bool ft_is_even(int nbr) { return ((EVEN(nbr)) ? TRUE : FALSE); }
int main(int argc,char **argv) {
 (void)argv;
 if(ft_is_even(argc-1)==TRUE) ft_putstr(EVEN_MSG); else ft_putstr(ODD_MSG);
 return SUCCESS;
}
'''
C08_EXERCISES['c08/ex01']=header_spec('ft_boolean.h',_h,[
 {'label':'nombre pair','argv':[],'expected':b'I have an even number of arguments.\n'},
 {'label':'nombre impair','argv':['a'],'expected':b'I have an odd number of arguments.\n'},
 {'label':'deux arguments','argv':['a','b'],'expected':b'I have an even number of arguments.\n'}],True)
_h=r'''#include "ft_abs.h"
#include "ft_abs.h"
int main(void) {
 int x=-5,y=7,z=0;
 return ABS(x)!=5 || ABS(y)!=7 || ABS(z)!=0 || ABS(-41)!=41;
}
'''
C08_EXERCISES['c08/ex02']=header_spec('ft_abs.h',_h,[{'label':'valeurs négatives, positives et zéro','expected':b''}],True)
_h=r'''#include "ft_point.h"
#include "ft_point.h"
void set_point(t_point *point) { point->x=42; point->y=21; }
int main(void) { t_point point; set_point(&point); return point.x!=42 || point.y!=21; }
'''
C08_EXERCISES['c08/ex03']=header_spec('ft_point.h',_h,[{'label':'structure et inclusions répétées','expected':b''}])

_STOCK=r'''#ifndef FT_STOCK_STR_H
#define FT_STOCK_STR_H
typedef struct s_stock_str { int size; char *str; char *copy; } t_stock_str;
#endif
'''
_helpers=r'''
#include "ft_stock_str.h"
#include <stdlib.h>
#include <string.h>
static int tab_case(int count)
{
 char a[]="hello",b[]="",c[]="42 piscine";char *av[]={a,b,c};int i,ok=1;
 t_stock_str *t=ft_strs_to_tab(count,av);
 if(!t)return 0;
 for(i=0;i<count;i++) {
  if(t[i].size!=(int)strlen(av[i]) || t[i].str!=av[i] || !t[i].copy || t[i].copy==av[i] || strcmp(t[i].copy,av[i]))ok=0;
 }
 if(t[count].str!=0)ok=0;
 for(i=0;i<count;i++)if(t[i].copy && t[i].copy!=av[i])free(t[i].copy);
 free(t);return ok;
}
'''
_branches=[('tableau vide','return tab_case(0);'),('une chaîne','return tab_case(1);'),('plusieurs chaînes','return tab_case(3);')]
_name='ft_strs_to_tab';_src=_name+'.c'
_decl='#include "ft_stock_str.h"\nstruct s_stock_str *ft_strs_to_tab(int, char **);'
_harness=_condition_harness(_decl,_branches,_helpers)
_cfg={'required_files':[_src],'exact_files':True,'sources':[_src],'build':'cc','binary':'test-stock',
      'provided_files':{'ft_stock_str.h':_STOCK},'allowed_functions':['malloc','free'],
      'prototype':_prototype(_name,'struct s_stock_str *','int, char **'), 'harness':_harness,
      'cases':[{'label':l,'argv':[str(i)],'expected':b'OK','marker':True,'code':73} for i,(l,_) in enumerate(_branches)],
      'style_files':[_src]}
C08_EXERCISES['c08/ex04']=project_spec(_src,'14',_cfg)

_h=r'''#include <unistd.h>
#include "ft_stock_str.h"
void ft_show_tab(struct s_stock_str *);
static const unsigned char marker[]={MARKER_BYTES};
int main(int argc,char **argv) {
 t_stock_str empty[]={{0,0,0}};
 t_stock_str a[]={{5,"hello","HELLO"},{0,"",""},{2,"42","XX"},{0,0,0}};
 if(argc!=2)return 2;
 if(argv[1][0]=='0')ft_show_tab(empty);
 else if(argv[1][0]=='1')ft_show_tab(a);
 else return 2;
 if(write(1,marker,sizeof marker)!=(ssize_t)sizeof marker)return 74;
 return 73;
}
'''
_src='ft_show_tab.c'
_cfg={'required_files':[_src],'exact_files':True,'sources':[_src],'build':'cc','binary':'test-show',
      'provided_files':{'ft_stock_str.h':_STOCK},'allowed_functions':['write'],
      'prototype':_prototype('ft_show_tab','void','struct s_stock_str *'),'harness':_h,
      'cases':[{'label':'tableau vide','argv':['0'],'expected':b'','marker':True,'code':73},
               {'label':'chaînes, copies et tailles','argv':['1'],'expected':b'hello\n5\nHELLO\n\n0\n\n42\n2\nXX\n','marker':True,'code':73}],
      'style_files':[_src]}
C08_EXERCISES['c08/ex05']=project_spec(_src,'14',_cfg)

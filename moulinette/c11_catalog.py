"""C 11 v8 : fonctions et callbacks ; do-op est dans le catalogue projet."""
from .c01_catalog import _spec

def spec(*a,**kw):
 s=_spec(*a,**kw);s['subject_version']='8.0';return s

C11_EXERCISES={}
_foreach=r'''
static int seen[16],nseen;
static void collect(int x) { if(nseen<16)seen[nseen++]=x; }
static int run_foreach(int n)
{
 int tab[]={5,-3,42,0}; nseen=0;ft_foreach(tab,n,collect);
 if(nseen!=n)return 0;
 for(int i=0;i<n;i++)if(seen[i]!=tab[i])return 0;
 return 1;
}
'''
C11_EXERCISES['c11/ex00']=spec('ft_foreach','void','int *, int, void (*)(int)',[('ordre et valeurs','return run_foreach(4);'),('taille nulle','return run_foreach(0);'),('un élément','return run_foreach(1);')],helpers=_foreach)
_map=r'''
#include <stdlib.h>
static int seen[16],nseen;
static int transform(int x) { if(nseen<16)seen[nseen++]=x; return x*3+1; }
static int run_map(void)
{
 int tab[]={5,-3,42,0},*p,i,ok=1; nseen=0;p=ft_map(tab,4,transform);
 if(!p || p==tab)return 0;
 if(nseen!=4)ok=0;
 for(i=0;i<4;i++)if(seen[i]!=tab[i] || p[i]!=tab[i]*3+1)ok=0;
 free(p);return ok;
}
'''
C11_EXERCISES['c11/ex01']=spec('ft_map','int *','int *, int, int (*)(int)',[('ordre et valeurs','return run_map();'),('un élément','int a[]={7};nseen=0;int *p=ft_map(a,1,transform);if(!p)return 0;int ok=p!=a && p[0]==22 && nseen==1 && seen[0]==7;free(p);return ok;')],helpers=_map,allowed=('malloc',))
_any=r'''
static int pred(char *s) { return s[0]=='x' ? -7 : 0; }
static char *ml_observed[8]; static int ml_observed_count;
static int ml_ordered_pred(char *s) { if(ml_observed_count<8)ml_observed[ml_observed_count]=s;ml_observed_count++;return pred(s); }
'''
C11_EXERCISES['c11/ex02']=spec('ft_any','int','char **, int (*)(char *)',[
 ('table vide','char *a[]={0};return ft_any(a,pred)==0;'),('aucun','char *a[]={"ab","bc",0};return ft_any(a,pred)==0;'),
 ('premier','char *a[]={"x","b",0};return ft_any(a,pred)==1;'),('dernier','char *a[]={"a","x",0};return ft_any(a,pred)==1;'),
 ('ordre callback sans correspondance','char *a[]={"a","b","c",0};ml_observed_count=0;int r=ft_any(a,ml_ordered_pred);return r==0 && ml_observed_count==3 && ml_observed[0]==a[0] && ml_observed[1]==a[1] && ml_observed[2]==a[2];'),
 ('ordre callback avec correspondance','char *a[]={"a","x","c",0};ml_observed_count=0;int r=ft_any(a,ml_ordered_pred);return r==1 && ml_observed_count>=2 && ml_observed_count<=3 && ml_observed[0]==a[0] && ml_observed[1]==a[1] && (ml_observed_count==2 || ml_observed[2]==a[2]);')],helpers=_any)
C11_EXERCISES['c11/ex03']=spec('ft_count_if','int','char **, int, int (*)(char *)',[
 ('zéro','char *a[]={"x","b","xx"};return ft_count_if(a,0,pred)==0;'),
 ('compte','char *a[]={"x","b","xx","a"};return ft_count_if(a,4,pred)==2;'),
 ('limite longueur','char *a[]={"a","b","xx"};return ft_count_if(a,2,pred)==0;'),
 ('ordre et valeurs du callback','char *a[]={"x","a","xx","x"};ml_observed_count=0;int r=ft_count_if(a,3,ml_ordered_pred);return r==2 && ml_observed_count==3 && ml_observed[0]==a[0] && ml_observed[1]==a[1] && ml_observed[2]==a[2];')],helpers=_any)
_cmp='static int cmp(int a,int b) { return (a>b)-(a<b); }\nstatic int cmp_wide(int a,int b) { return a>b ? 42 : a<b ? -17 : 0; }'
C11_EXERCISES['c11/ex04']=spec('ft_is_sort','int','int *, int, int (*)(int, int)',[
 ('vide','int a[]={1};return ft_is_sort(a,0,cmp)==1;'),('un','int a[]={1};return ft_is_sort(a,1,cmp)==1;'),
 ('croissant','int a[]={-2,0,0,4};return ft_is_sort(a,4,cmp)==1;'),('décroissant','int a[]={4,1,1,-3};return ft_is_sort(a,4,cmp)==1;'),
 ('désordonné','int a[]={1,3,2};return ft_is_sort(a,3,cmp)==0;'),
 ('comparateur non normalisé','int a[]={-3,0,0,9},b[]={1,3,2};return ft_is_sort(a,4,cmp_wide)==1 && ft_is_sort(b,3,cmp_wide)==0;')],helpers=_cmp)
_sort=r'''
#include <string.h>
static int cmp_forward(char *a,char *b) { return strcmp(a,b); }
static int cmp_reverse(char *a,char *b) { return strcmp(b,a); }
static int sort_case(int reverse)
{
 char x[]="z",y[]="a",z[]="AA",w[]="b";
 char *tab[]={x,y,z,w,0};char **expected;
 char *forward[]={z,y,w,x,0};char *backward[]={x,w,y,z,0};int i;
 expected=reverse?backward:forward;
 SORT_CALL
 for(i=0;i<5;i++)if(tab[i]!=expected[i])return 0;
 return strcmp(x,"z")==0 && strcmp(y,"a")==0 && strcmp(z,"AA")==0 && strcmp(w,"b")==0;
}
'''
# A static unused comparator would be rejected by -Werror: keep only those needed.
simple=_sort.replace('static int cmp_forward(char *a,char *b) { return strcmp(a,b); }\n','').replace('static int cmp_reverse(char *a,char *b) { return strcmp(b,a); }\n','').replace('SORT_CALL','ft_sort_string_tab(tab);')
C11_EXERCISES['c11/ex06']=spec('ft_sort_string_tab','void','char **',[('ordre ASCII et pointeurs','return sort_case(0);'),('table vide et un élément','char x[]="z";char *a[]={0},*b[]={x,0};ft_sort_string_tab(a);ft_sort_string_tab(b);return !a[0] && b[0]==x && !b[1] && x[0]==122 && x[1]==0;')],helpers=simple)
advanced=_sort.replace('SORT_CALL','ft_advanced_sort_string_tab(tab,reverse?cmp_reverse:cmp_forward);')
C11_EXERCISES['c11/ex07']=spec('ft_advanced_sort_string_tab','void','char **, int (*)(char *, char *)',[
 ('comparateur croissant','return sort_case(0);'),('comparateur décroissant','return sort_case(1);'),
 ('table vide et un élément','char x[]="z";char *a[]={0},*b[]={x,0};ft_advanced_sort_string_tab(a,cmp_forward);ft_advanced_sort_string_tab(b,cmp_forward);return !a[0] && b[0]==x && !b[1] && x[0]==122 && x[1]==0;')],helpers=advanced)

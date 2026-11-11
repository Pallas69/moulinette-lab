"""C 07 v6 : tests pédagogiques partiels d'allocation, rendus de confiance."""
from .c01_catalog import _spec

def spec(*a,**kw):
 kw['allowed']=('malloc',)
 s=_spec(*a,**kw);s['subject_version']='6';return s

_strdup=r'''
#include <string.h>
#include <stdlib.h>
static int dup_case(char *s)
{
    char before[64],*ro,*p; size_t len=strlen(s); if(len>=sizeof before)return 0;
    memcpy(before,s,len+1);ro=ml_ro_str(before);p=ft_strdup(ro);if(!p)return 0;
    if(p==ro || strcmp(p,before)) {if(p!=ro)free(p);return 0;}
    if(len) {p[0]='Q';}
    free(p);return ml_unfreed_count()==0;
}
'''
C07_EXERCISES={}
C07_EXERCISES['c07/ex00']=spec('ft_strdup','char *','char *',[
 ('chaîne vide','char s[]="";return dup_case(s);'),('texte','char s[]="bonjour 42";return dup_case(s);'),
 ('NUL interne',"char s[]={'a',0,'b',0};return dup_case(s)&&s[2]=='b';"),
 ('octets élevés',"char s[]={(char)0x80,(char)0xff,0};return dup_case(s);")],helpers=_strdup)
_range=r'''
#include <stdlib.h>
static int range_case(int lo,int hi)
{
    int *p=ft_range(lo,hi),i;
    if(lo>=hi)return p==NULL;
    if(!p)return 0;
    for(i=0;i<hi-lo;i++)if(p[i]!=lo+i){free(p);return 0;}
    free(p);return 1;
}
'''
C07_EXERCISES['c07/ex01']=spec('ft_range','int *','int, int',[
 ('vide','return range_case(2,2);'),('inversé','return range_case(8,1);'),('un élément','return range_case(4,5);'),
 ('négatifs','return range_case(-5,3);'),('positifs','return range_case(10,25);')],helpers=_range)
_ultimate=r'''
#include <stdlib.h>
static int range_case(int lo,int hi)
{
    int x=42,*p=&x,i,ret=ft_ultimate_range(&p,lo,hi);
    if(lo>=hi)return ret==0 && p==NULL;
    if(ret!=hi-lo || !p || p==&x)return 0;
    for(i=0;i<ret;i++)if(p[i]!=lo+i){free(p);return 0;}
    free(p);return 1;
}
'''
C07_EXERCISES['c07/ex02']=spec('ft_ultimate_range','int','int **, int, int',[
 ('vide','return range_case(2,2);'),('inversé','return range_case(8,1);'),('un élément','return range_case(4,5);'),
 ('négatifs','return range_case(-5,3);'),('positifs','return range_case(10,25);')],helpers=_ultimate)
_join=r'''
#include <string.h>
#include <stdlib.h>
static int join_case(int n,char **a,char *sep,const char *expected)
{
    char *p=ft_strjoin(n,a,sep);int ok;if(!p)return 0;
    ok=strcmp(p,expected)==0;free(p);return ok;
}
'''
C07_EXERCISES['c07/ex03']=spec('ft_strjoin','char *','int, char **, char *',[
 ('aucune chaîne','char *a[]={NULL};return join_case(0,a,",","");'),
 ('une chaîne','char *a[]={"bonjour"};return join_case(1,a,",","bonjour");'),
 ('chaînes et séparateur','char *a[]={"a","b","c"};return join_case(3,a,"-","a-b-c");'),
 ('chaînes vides','char *a[]={"","a",""};return join_case(3,a,"::","::a::");'),
 ('séparateur vide','char *a[]={"a","b","c"};return join_case(3,a,"","abc");')],helpers=_join)
_split=r'''
#include <string.h>
#include <stdlib.h>
static int split_case(char *s,char *sep,const char **expect,int count)
{
    char before[256]; char **p; int i,ok=1;
    if(strlen(s)>=sizeof before) return 0;
    strcpy(before,s);
    p=ft_split(s,sep);if(!p)return 0;
    if(strcmp(s,before)!=0)ok=0;
    for(i=0;i<count;i++)if(!p[i] || strcmp(p[i],expect[i])) {ok=0;break;}
    if(ok && p[count]!=NULL)ok=0;
    /* Libérer uniquement les entrées dont l'existence a été vérifiée. */
    for(i=0;i<count && p[i];i++) { free(p[i]); }
    free(p);return ok;
}
'''
C07_EXERCISES['c07/ex05']=spec('ft_split','char **','char *, char *',[
 ('chaîne vide','char s[]="",sep[]=",";const char *e[]={0};return split_case(s,sep,e,0);'),
 ('sans séparateur','char s[]="abc",sep[]=",";const char *e[]={"abc"};return split_case(s,sep,e,1);'),
 ('plusieurs séparateurs','char s[]=",,alpha;beta,,gamma;",sep[]=",;";const char *e[]={"alpha","beta","gamma"};return split_case(s,sep,e,3);'),
 ('séparateurs seulement','char s[]=",,,",sep[]=",";const char *e[]={0};return split_case(s,sep,e,0);'),
 ('charset vide','char s[]="a b",sep[]="";const char *e[]={"a b"};return split_case(s,sep,e,1);')],helpers=_split)

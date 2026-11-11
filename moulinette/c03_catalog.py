"""C 03 v5 : tests locaux non officiels ; chaînes et tampons valides."""
from .c01_catalog import _spec

C03_EXERCISES={}

def spec(name,ret,params,branches,**kw):
    result=_spec(name,ret,params,branches,**kw);result['subject_version']='5';return result

_comp=r'''
#include <string.h>
static int sign(int x) { return (x>0)-(x<0); }
static int compare_cases(int limited)
{
    const char *values[]={"", "a", "ab", "abc", "abd", "ABC", "z", "\200", "\377", "a\377"};
    unsigned int i,j,n;
    for(i=0;i<sizeof values/sizeof *values;i++) for(j=0;j<sizeof values/sizeof *values;j++) {
        char a[32],b[32],aa[32],bb[32];
        strcpy(a,values[i]); strcpy(b,values[j]); strcpy(aa,a); strcpy(bb,b);
        if(!limited && sign(ft_strcmp(a,b))!=sign(strcmp(a,b))) return 0;
        if(limited) for(n=0;n<8;n++) if(sign(ft_strncmp(a,b,n))!=sign(strncmp(a,b,n))) return 0;
        if(strcmp(a,aa)||strcmp(b,bb)) return 0;
    }
    return 1;
}
'''
def _comp_helpers(name):
    helper=_comp
    if name=='ft_strcmp':
        helper=helper.replace('ft_strncmp(a,b,n)','strncmp(a,b,n)')
    else:
        helper=helper.replace('ft_strcmp(a,b)','strcmp(a,b)')
    return helper
for i,name,params,limited in [(0,'ft_strcmp','char *, char *',0),(1,'ft_strncmp','char *, char *, unsigned int',1)]:
    C03_EXERCISES[f'c03/ex{i:02}']=spec(name,'int',params,[('comparaisons ASCII et octets élevés',f'return compare_cases({limited});')],helpers=_comp_helpers(name))

_concat=r'''
#include <string.h>
static int concat_case(const char *prefix,const char *suffix,unsigned int n)
{
    char dest[64], expect[64],src[32],before[32]; unsigned int i=0,j=0,d=0,l;
    memset(dest,0x53,sizeof dest);strcpy(dest,prefix);memcpy(expect,dest,sizeof dest);
    memset(src,0x69,sizeof src);strcpy(src,suffix);memcpy(before,src,sizeof src);
    while(expect[d]) d++;
    l=(unsigned int)strlen(src);
    REFERENCE
    CALL
    return memcmp(dest,expect,sizeof dest)==0 && memcmp(src,before,sizeof src)==0;
}
'''
for i,name,params in [(2,'ft_strcat','char *, char *'),(3,'ft_strncat','char *, char *, unsigned int'),(5,'ft_strlcat','char *, char *, unsigned int')]:
    if i==2:
        ref='(void)n; (void)i; (void)l; while(src[j]) expect[d++]=src[j++]; expect[d]=0;'
        call='if(ft_strcat(dest,src)!=dest) return 0;'
    elif i==3:
        ref='(void)i; (void)l; while(j<n && src[j]) expect[d++]=src[j++]; expect[d]=0;'
        call='if(ft_strncat(dest,src,n)!=dest) return 0;'
    else:
        ref='i=d; if(i>n) i=n; if(d<n) { while(j<l && d+j+1<n) { expect[d+j]=src[j];j++; } expect[d+j]=0; }'
        call='if(ft_strlcat(dest,src,n)!=i+l) return 0;'
    helper=_concat.replace('REFERENCE',ref).replace('CALL',call)
    tests=[('vides','','',0),('ajout classique','abc','XYZ',8),('destination vide','','abc',4),('source vide','abc','',8),('taille zéro','abc','xyz',0),('taille un','abc','xyz',1),('taille égale à destination','abc','xyz',3),('troncature','abc','xyz',5),('taille exacte','abc','xyz',7),('octets élevés',r'a\200',r'b\377',8)]
    branches=[(label,f'return concat_case("{a}","{b}",{n});') for label,a,b,n in tests]
    C03_EXERCISES[f'c03/ex{i:02}']=spec(name,'unsigned int' if i==5 else 'char *',params,branches,helpers=helper)

_strstr=r'''
#include <string.h>
static int find_case(const char *text,const char *pattern)
{
    char s[64],t[64],a[64],b[64]; char *want,*got;
    strcpy(s,text);strcpy(t,pattern);strcpy(a,s);strcpy(b,t);
    want=strstr(s,t);got=ft_strstr(s,t);
    return got==want && strcmp(a,s)==0 && strcmp(b,t)==0;
}
'''
C03_EXERCISES['c03/ex04']=spec('ft_strstr','char *','char *, char *',[
 ('vide dans vide','return find_case("","");'),('motif vide','return find_case("abc","");'),
 ('début','return find_case("abcde","abc");'),('milieu','return find_case("abcde","bcd");'),
 ('fin','return find_case("abcde","de");'),('absent','return find_case("abcde","xyz");'),
 ('première occurrence','return find_case("ababab","ab");'),('chevauchement','return find_case("aaab","aab");'),
 ('motif plus long','return find_case("abc","abcd");'),('octets élevés',r'return find_case("a\200\377b","\200\377");')],helpers=_strstr)

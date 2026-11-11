"""C Piscine C 02 v6. Tests pédagogiques non officiels ; chaînes ASCII.

Les tampons sont suffisamment dimensionnés et distincts. Aucun chevauchement,
argument NULL ou pointeur invalide n'est exigé par les sujets de copie.
"""
from .c01_catalog import _prototype, _spec

C02_EXERCISES = {}

_copy_helpers = r'''
#include <string.h>
static int copy_case(const char *input, unsigned int n, int kind)
{
    char src[32], before[32], dest[32], expect[32];
    unsigned int i, len;
    memset(src, 0x5a, sizeof src); memcpy(src,input,strlen(input)+1);
    memcpy(before,src,sizeof src); memset(dest,0x6b,sizeof dest);
    memcpy(expect,dest,sizeof dest); len=(unsigned int)strlen(src);
    if(kind==0) {
        memcpy(expect,src,len+1);
        if(ft_strcpy(dest,src)!=dest) return 0;
    } else if(kind==1) {
        for(i=0;i<n;i++) expect[i]=(i<len)?src[i]:0;
        if(ft_strncpy(dest,src,n)!=dest) return 0;
    } else {
        if(n) { for(i=0;i+1<n && i<len;i++) expect[i]=src[i]; expect[i]=0; }
        if(ft_strlcpy(dest,src,n)!=len) return 0;
    }
    return memcmp(expect,dest,sizeof dest)==0 && memcmp(before,src,sizeof src)==0;
}
'''
# The two non-target operations use private reference names: a submitted file
# may legitimately define additional helpers with public names of its own.
def _copy_helpers_for(current):
    refs={
      'ft_strcpy':'static char *_ml_ref_strcpy(char *d,char *s) { char *r=d; while((*d++=*s++)) {} return r; }',
      'ft_strncpy':'static char *_ml_ref_strncpy(char *d,char *s,unsigned int n) { unsigned int i=0; while(i<n && s[i]) { d[i]=s[i]; i++; } while(i<n) d[i++]=0; return d; }',
      'ft_strlcpy':'static unsigned int _ml_ref_strlcpy(char *d,char *s,unsigned int n) { unsigned int i=0,l=0; while(s[l]) l++; if(n) { while(i+1<n && s[i]) { d[i]=s[i]; i++; } d[i]=0; } return l; }'}
    helper=_copy_helpers
    for name in refs:
        if name != current:
            helper=helper.replace(name+'(', '_ml_ref_'+name[3:]+'(')
    return '\n'.join(v for k,v in refs.items() if k != current)+'\n'+helper

for ident,name,ret,params,kind in [
    ('c02/ex00','ft_strcpy','char *','char *, char *',0),
    ('c02/ex01','ft_strncpy','char *','char *, char *, unsigned int',1),
    ('c02/ex10','ft_strlcpy','unsigned int','char *, char *, unsigned int',2)]:
    data=[('chaîne vide','',0),('une lettre','x',1),('texte complet','Hello 42!',15),
          ('taille zéro','abcdef',0),('taille un','abcdef',1),('troncature','abcdef',3),
          ('taille exacte','abcdef',6),('taille avec NUL','abcdef',7),('taille supérieure','abcdef',12),
          ('octets non ASCII',r'\200\377z',6)]
    branches=[(label, f'return copy_case("{s}",{n},{kind});') for label,s,n in data]
    C02_EXERCISES[ident]=_spec(name,ret,params,branches,helpers=_copy_helpers_for(name))

_class_helpers=r'''
static int class_case(int which, int (*fn)(char *))
{
    int i, want, result;
    char text[4];
    text[0]=0;
    if(fn(text)!=1) return 0;
    for(i=1;i<256;i++) {
        text[0]=(char)i; text[1]=0; text[2]='X'; text[3]=0;
        if(which==0) want=(i>='A'&&i<='Z')||(i>='a'&&i<='z');
        else if(which==1) want=(i>='0'&&i<='9');
        else if(which==2) want=(i>='a'&&i<='z');
        else if(which==3) want=(i>='A'&&i<='Z');
        else want=(i>=32&&i<=126);
        result=fn(text);
        if(result!=want || (unsigned char)text[0]!=(unsigned int)i || text[1]!=0 || text[2]!='X') return 0;
    }
    return 1;
}
'''
for i,name in enumerate(['ft_str_is_alpha','ft_str_is_numeric','ft_str_is_lowercase','ft_str_is_uppercase','ft_str_is_printable']):
    C02_EXERCISES[f'c02/ex{i+2:02}']=_spec(name,'int','char *',[
        ('chaîne vide et octets individuels',f'return class_case({i},{name});'),
        ('texte mixte valide et invalide',f'char a[]="abcZ8 "; return {name}(a)==0;'),
        ('fin au premier NUL',f"char a[]={{0,1,0}}; return {name}(a)==1 && a[1]==1;")],helpers=_class_helpers)
# Printable includes a space, so that mixed string is valid there.
C02_EXERCISES['c02/ex06']=_spec('ft_str_is_printable','int','char *',[
    ('chaîne vide et octets individuels','return class_case(4,ft_str_is_printable);'),
    ('texte imprimable','char a[]="abcZ8 !~"; return ft_str_is_printable(a)==1;'),
    ('contrôle en milieu de chaîne','char a[]={\'a\',1,\'b\',0}; return ft_str_is_printable(a)==0;'),
    ('fin au premier NUL',"char a[]={0,1,0}; return ft_str_is_printable(a)==1 && a[1]==1;")],helpers=_class_helpers)

_case_helpers=r'''
static int case_bytes(int upper, char *(*fn)(char *))
{
    int i,want;
    char s[4];
    for(i=1;i<256;i++) {
        s[0]=(char)i; s[1]=0; s[2]='X'; s[3]=0;
        want=i;
        if(upper && i>='a' && i<='z') want=i-32;
        if(!upper && i>='A' && i<='Z') want=i+32;
        if(fn(s)!=s || (unsigned char)s[0]!=(unsigned int)want || s[1]!=0 || s[2]!='X') return 0;
    }
    s[0]=0; return fn(s)==s && s[0]==0;
}
'''
for ident,name,upper in [('c02/ex07','ft_strupcase',1),('c02/ex08','ft_strlowcase',0)]:
    C02_EXERCISES[ident]=_spec(name,'char *','char *',[
        ('tous les octets et retour',f'return case_bytes({upper},{name});'),
        ('texte mixte',f'char s[]="aZ 42!"; char *r={name}(s); return r==s && s[0]==\'{"A" if upper else "a"}\' && s[1]==\'{"Z" if upper else "z"}\' && s[2]==\' \';')],helpers=_case_helpers)

_cap_helpers=r'''
#include <string.h>
static int cap_case(char *s, const char *expected)
{
    char *p=ft_strcapitalize(s);
    return p==s && strcmp(s,expected)==0;
}
'''
C02_EXERCISES['c02/ex09']=_spec('ft_strcapitalize','char *','char *',[
    ('exemple du sujet','char s[]="hi, how are you? 42words forty-two; fifty+and+one"; return cap_case(s,"Hi, How Are You? 42words Forty-Two; Fifty+And+One");'),
    ('chaîne vide','char s[]=""; return cap_case(s,"");'),
    ('début numérique','char s[]="42HELLO 3WORDS"; return cap_case(s,"42hello 3words");'),
    ('séparateurs','char s[]="hELLO__wORLD!abc\tXY"; return cap_case(s,"Hello__World!Abc\tXy");'),
    ('octets élevés comme séparateurs',"char s[]={'a',(char)0xff,'b','C',0}; char e[]={'A',(char)0xff,'B','c',0}; return cap_case(s,e);"),
    ('NUL interne',"char s[]={'a','B',0,'Z',0}; return ft_strcapitalize(s)==s && s[0]=='A' && s[1]=='b' && s[2]==0 && s[3]=='Z';")],helpers=_cap_helpers)

_put_harness=r'''#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_putstr_non_printable(char *str);
int main(int argc, char **argv)
{
    char with_nul[] = {'a',0,'b',0};
    char bytes[] = {1, 9, 10, 31, 32, 126, 127, (char)128, (char)255, 0};
    if (argc != 2) return 2;
    switch(argv[1][0]) {
    case '0': ft_putstr_non_printable(""); break;
    case '1': ft_putstr_non_printable("Hello\nHow are you?"); break;
    case '2': ft_putstr_non_printable(bytes); break;
    case '3': ft_putstr_non_printable(with_nul); break;
    case '4': ft_putstr_non_printable("a"); ft_putstr_non_printable("b"); break;
    default: return 2;
    }
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''
C02_EXERCISES['c02/ex11']={'source':'ft_putstr_non_printable.c','executable':'test-ft_putstr_non_printable','subject_version':'6',
    'allowed_functions':{'write'},'prototype':_prototype('ft_putstr_non_printable','void','char *'), 'harness':_put_harness,
    'cases':[('chaîne vide','0',b''),('exemple du sujet','1',b'Hello\\0aHow are you?'),
        ('bornes et octets élevés','2',b'\\01\\09\\0a\\1f ~\\7f\\80\\ff'),('premier NUL','3',b'a'),('deux appels','4',b'ab')]}

_memory_helpers=r'''
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
static int hexval(unsigned char c)
{
    if(c>='0' && c<='9') return c-'0';
    if(c>='a' && c<='f') return c-'a'+10;
    if(c>='A' && c<='F') return c-'A'+10;
    return -1;
}
static int memory_output(const unsigned char *p, unsigned int n, const char *out, size_t len)
{
    size_t pos=0; unsigned int off=0,i,count; uintptr_t address; int d,digits;
    while(off<n) {
        address=0; digits=0;
        if(pos+2<=len && out[pos]=='0' && (out[pos+1]=='x' || out[pos+1]=='X')) pos+=2;
        while(pos<len && (d=hexval((unsigned char)out[pos]))>=0) {
            if(address > (UINTPTR_MAX-(uintptr_t)d)/16) return 0;
            address=address*16+(uintptr_t)d; pos++; digits++;
        }
        if(!digits || address!=(uintptr_t)(p+off) || pos+2>len || out[pos++]!=':' || out[pos++]!=' ') return 0;
        count=n-off; if(count>16) count=16;
        for(i=0;i<16;i++) {
            if(pos+2>len) return 0;
            if(i<count) {
                int a=hexval((unsigned char)out[pos]),b=hexval((unsigned char)out[pos+1]);
                if(a<0 || b<0 || (unsigned int)(a*16+b)!=(unsigned int)p[off+i]) return 0;
            } else if(out[pos]!=' ' || out[pos+1]!=' ') return 0;
            pos+=2;
            if(i%2==1 && (pos>=len || out[pos++]!=' ')) return 0;
        }
        for(i=0;i<count;i++) {
            unsigned char c=p[off+i];
            if(pos>=len || out[pos++] != (char)((c>=32 && c<=126)?c:'.')) return 0;
        }
        if(pos>=len || out[pos++]!='\n') return 0;
        off+=count;
    }
    return pos==len;
}
static int memory_case(unsigned int n)
{
    unsigned char bytes[40]={0,1,9,10,31,32,33,48,65,90,97,122,126,127,128,255,
                             66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84};
    unsigned char before[40]; char output[2048]; int fd[2],saved; ssize_t total=0,got; void *r;
    memcpy(before,bytes,sizeof bytes);
    if(pipe(fd)<0) return 0;
    saved=dup(1); if(saved<0) { close(fd[0]); close(fd[1]); return 0; }
    fflush(stdout);
    if(dup2(fd[1],1)<0) { close(saved);close(fd[0]);close(fd[1]);return 0; }
    close(fd[1]); r=ft_print_memory(bytes,n); fflush(stdout);
    if(dup2(saved,1)<0) { close(saved); close(fd[0]); return 0; }
    close(saved);
    while(total<(ssize_t)sizeof output && (got=read(fd[0],output+total,sizeof output-(size_t)total))>0) total+=got;
    close(fd[0]);
    return r==bytes && memcmp(before,bytes,sizeof bytes)==0 && memory_output(bytes,n,output,(size_t)total);
}
'''
C02_EXERCISES['c02/ex12']=_spec('ft_print_memory','void *','void *, unsigned int',[
    ('taille zéro','return memory_case(0);'),('un octet','return memory_case(1);'),
    ('deux octets','return memory_case(2);'),('ligne presque pleine','return memory_case(15);'),
    ('ligne complète','return memory_case(16);'),('deux lignes','return memory_case(17);'),
    ('deux lignes complètes','return memory_case(32);'),('trois lignes','return memory_case(33);')],allowed=('write',),helpers=_memory_helpers)

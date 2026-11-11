"""C 05 v7 : cas arithmétiques non officiels, sans débordement."""
from .c01_catalog import _spec

def spec(*a,**kw):
 s=_spec(*a,**kw);s['subject_version']='7';return s

C05_EXERCISES={}
for i,name in enumerate(('ft_iterative_factorial','ft_recursive_factorial')):
 pairs=[(-3,0),(0,1),(1,1),(2,2),(3,6),(5,120),(6,720),(10,3628800),(11,39916800),(12,479001600)]
 C05_EXERCISES[f'c05/ex{i:02}']=spec(name,'int','int',[(f'fact({n})',f'return {name}({n})=={v};') for n,v in pairs])
for i,name in [(2,'ft_iterative_power'),(3,'ft_recursive_power')]:
 pairs=[(0,0,1),(0,3,0),(2,0,1),(2,-1,0),(-3,3,-27),(-2,3,-8),(-2,4,16),(10,6,1000000),(1,20,1)]
 C05_EXERCISES[f'c05/ex{i:02}']=spec(name,'int','int, int',[(f'{a} puissance {b}',f'return {name}({a},{b})=={v};') for a,b,v in pairs])
C05_EXERCISES['c05/ex04']=spec('ft_fibonacci','int','int',[(f'indice {n}',f'return ft_fibonacci({n})=={v};') for n,v in [(-4,-1),(0,0),(1,1),(2,1),(3,2),(5,5),(10,55),(20,6765)]])
C05_EXERCISES['c05/ex05']=spec('ft_sqrt','int','int',[(f'racine de {n}',f'return ft_sqrt({n})=={v};') for n,v in [(-5,0),(0,0),(1,1),(2,0),(9,3),(15,0),(120,0),(121,11),(144,12),(2147395600,46340)]])
C05_EXERCISES['c05/ex06']=spec('ft_is_prime','int','int',[(f'premier {n}',f'return ft_is_prime({n})=={v};') for n,v in [(-17,0),(0,0),(1,0),(2,1),(3,1),(4,0),(25,0),(37,1),(49,0),(97,1),(100,0),(104729,1)]])
C05_EXERCISES['c05/ex07']=spec('ft_find_next_prime','int','int',[(f'prochain premier depuis {n}',f'return ft_find_next_prime({n})=={v};') for n,v in [(-17,2),(0,2),(1,2),(2,2),(3,3),(4,5),(14,17),(90,97),(97,97),(100,101),(104700,104701)]])
_queens=r'''
#include <stdio.h>
#include <string.h>
static int queens_case(void)
{
    FILE *tmp; int saved,ret,count=0,i,j; char rows[724][11],line[32];
    tmp=tmpfile(); if(!tmp) return 0;
    saved=dup(1); if(saved<0) {fclose(tmp);return 0;}
    fflush(stdout); if(dup2(fileno(tmp),1)<0) {close(saved);fclose(tmp);return 0;}
    ret=ft_ten_queens_puzzle();fflush(stdout);
    if(dup2(saved,1)<0) {close(saved);fclose(tmp);return 0;}
    close(saved);rewind(tmp);
    while(fgets(line,sizeof line,tmp)) {
        if(count>=724 || strlen(line)!=11 || line[10]!='\n') {fclose(tmp);return 0;}
        for(i=0;i<10;i++) {
            if(line[i]<'0'||line[i]>'9') {fclose(tmp);return 0;}
            for(j=0;j<i;j++) if(line[i]==line[j] || line[i]-line[j]==i-j || line[j]-line[i]==i-j) {fclose(tmp);return 0;}
        }
        for(i=0;i<count;i++) if(memcmp(rows[i],line,10)==0) {fclose(tmp);return 0;}
        memcpy(rows[count++],line,10);
    }
    fclose(tmp);return ret==724 && count==724;
}
'''
# fileno() is POSIX; define its feature level before any header in the harness.
_queens=_queens.replace('#include <stdio.h>','#include <stdio.h>\nextern int fileno(FILE *);')
C05_EXERCISES['c05/ex08']=spec('ft_ten_queens_puzzle','int','void', [('724 placements valides et distincts','return queens_case();')],allowed=('write',),helpers=_queens)
C05_EXERCISES['c05/ex08']['timeout']=4

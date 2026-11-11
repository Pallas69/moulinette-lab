"""C Piscine C 01 v6 : harnais de confiance et jeux d'essai non officiels.

Fondé sur le PDF fourni. Pas de division par zéro, d'alias ambigu pour les
sorties division, ni de pointeur invalide : ces cas ne sont pas spécifiés.
"""


from .c_memguard import MEMGUARD_C


def _prototype(name, return_type, params, extra_undef=()):
    signature = return_type + ' (*)(' + params + ')'
    undef = '\n'.join('#undef ' + x for x in ('int', 'char', 'void', name, '_Generic', '_Static_assert', *extra_undef))
    return f'''#include "{name}.c"
{undef}
_Static_assert(_Generic(&{name}, {signature}: 1, default: 0), "Prototype attendu : {name}");
'''


def _condition_harness(declaration, branches, helpers=''):
    cases = '\n'.join(f"case {i}: {{ {body} }}" for i, (_, body) in enumerate(branches))
    return '''#include <limits.h>
#include <unistd.h>
''' + MEMGUARD_C + '\n' + declaration + '\n' + helpers + r'''
static const unsigned char marker[] = { MARKER_BYTES };
static int run_case(unsigned int choice)
{
    switch (choice) {
''' + cases + r'''
    default: return 0;
    }
}
int main(int argc, char **argv)
{
    int ok; unsigned int choice=0; const char *p;
    if (argc != 2 || !argv[1][0]) return 2;
    p=argv[1];
    while (*p) {
        if (*p<'0' || *p>'9' || choice>9999) return 2;
        choice=choice*10+(unsigned int)(*p-'0');p++;
    }
    ok = run_case(choice);
    if (write(1, ok ? "OK" : "KO", 2) != 2) return 74;
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''


def _spec(name, return_type, params, branches, *, allowed=(), helpers='', declaration=None):
    return {'source':name+'.c', 'executable':'test-'+name, 'subject_version':'6',
            'allowed_functions':set(allowed), 'prototype':_prototype(name,return_type,params),
            'harness':_condition_harness(declaration or (return_type+' '+name+'('+params+');'),branches,helpers),
            'cases':[(label,str(i),b'OK') for i,(label,_) in enumerate(branches)]}

C01_EXERCISES={}
C01_EXERCISES['c01/ex00']=_spec('ft_ft','void','int *',[
    ('valeur positive','int x=17; ft_ft(&x); return x==42;'),
    ('valeur négative','int x=-9; ft_ft(&x); return x==42;'),
    ('valeur initiale zéro','int x=0; ft_ft(&x); return x==42;'),
    ('deux entiers distincts','int x=1,y=2; ft_ft(&x); ft_ft(&y); return x==42 && y==42;')])

_pointer_decls='int *p1=&x; int **p2=&p1; int ***p3=&p2; int ****p4=&p3; int *****p5=&p4; int ******p6=&p5; int *******p7=&p6; int ********p8=&p7;'
C01_EXERCISES['c01/ex01']=_spec('ft_ultimate_ft','void','int *********',[
    ('pointeur de profondeur neuf',f'int x=0; {_pointer_decls} ft_ultimate_ft(&p8); return x==42;'),
    ('valeur négative',f'int x=-27; {_pointer_decls} ft_ultimate_ft(&p8); return x==42;')])
C01_EXERCISES['c01/ex02']=_spec('ft_swap','void','int *, int *',[
    ('deux valeurs','int a=12,b=-4; ft_swap(&a,&b); return a==-4 && b==12;'),
    ('valeurs égales','int a=9,b=9; ft_swap(&a,&b); return a==9 && b==9;'),
    ('bornes int','int a=INT_MIN,b=INT_MAX; ft_swap(&a,&b); return a==INT_MAX && b==INT_MIN;'),
    ('même adresse','int a=7; ft_swap(&a,&a); return a==7;')])

_pairs=[('division exacte',12,3,4,0),('division avec reste',17,5,3,2),
        ('dividende négatif',-11,3,-3,-2),('diviseur négatif',11,-3,-3,2),
        ('deux négatifs',-11,-3,3,-2),('dividende nul',0,5,0,0),('diviseur plus grand',3,10,0,3)]
C01_EXERCISES['c01/ex03']=_spec('ft_div_mod','void','int, int, int *, int *',[
    (label,f'int d=987,m=876; ft_div_mod({a},{b},&d,&m); return d=={q} && m=={r};') for label,a,b,q,r in _pairs])
C01_EXERCISES['c01/ex04']=_spec('ft_ultimate_div_mod','void','int *, int *',[
    (label,f'int a={a},b={b}; ft_ultimate_div_mod(&a,&b); return a=={q} && b=={r};') for label,a,b,q,r in _pairs])

_put_harness=r'''#include <unistd.h>
static const unsigned char marker[] = { MARKER_BYTES };
void ft_putstr(char *str);
int main(int argc, char **argv)
{
    char with_nul[] = {'a',0,'b',0};
    char bytes[] = {(char)0x80,(char)0xff,0};
    if (argc != 2) return 2;
    switch(argv[1][0]) {
    case '0': ft_putstr(""); break;
    case '1': ft_putstr("Hello!"); break;
    case '2': ft_putstr("A\n\tB"); break;
    case '3': ft_putstr(with_nul); break;
    case '4': ft_putstr(bytes); break;
    case '5': ft_putstr("a"); ft_putstr("b"); break;
    default: return 2;
    }
    if (write(1, marker, sizeof(marker)) != (ssize_t)sizeof(marker)) return 74;
    return 73;
}
'''
C01_EXERCISES['c01/ex05']={'source':'ft_putstr.c','executable':'test-ft_putstr','subject_version':'6',
    'allowed_functions':{'write'}, 'prototype':_prototype('ft_putstr','void','char *'), 'harness':_put_harness,
    'cases':[('chaîne vide','0',b''),('texte simple','1',b'Hello!'),('saut et tabulation','2',b'A\n\tB'),
             ('fin au premier NUL','3',b'a'),('octets non ASCII','4',bytes((128,255))),('deux appels','5',b'ab')]}
C01_EXERCISES['c01/ex06']=_spec('ft_strlen','int','char *',[
    ('chaîne vide','char s[]=""; return ft_strlen(s)==0;'),
    ('texte','char s[]="bonjour"; return ft_strlen(s)==7;'),
    ('fin au premier NUL',"char s[]={'a',0,'b',0}; return ft_strlen(s)==1;"),
    ('espaces et nouvelle ligne','char s[]="a b\\nc"; return ft_strlen(s)==5;'),
    ('octets non ASCII',"char s[]={(char)0x80,(char)0xff,0}; return ft_strlen(s)==2;"),
    ('appels multiples','char a[]="a",b[]="abcd"; return ft_strlen(a)==1 && ft_strlen(b)==4;')])

_arrays=[('taille nulle',[12],0),('un élément',[7],1),('deux éléments',[4,1],2),
         ('taille impaire',[3,-2,7,0,1],5),('doublons',[4,4,-1,4,-1,0],6),
         ('valeurs int extrêmes',['INT_MAX','INT_MIN',0],3),('déjà ordonné',[-3,-1,0,2],4)]

def _array_branch(name,arr,n,expected):
    values=','.join(map(str,arr)); results=','.join(map(str,expected))
    return ('struct data { int before; int tab['+str(len(arr))+']; int after; }; '
            'struct data d={12345,{'+values+'},54321}; int expected[]={'+results+'}; int i; '
            +name+'(d.tab,'+str(n)+'); if(d.before!=12345 || d.after!=54321) return 0; '
            'for(i=0;i<'+str(len(arr))+';++i) if(d.tab[i]!=expected[i]) return 0; return 1;')

for ident,name in [('c01/ex07','ft_rev_int_tab'),('c01/ex08','ft_sort_int_tab')]:
    branches=[]
    for label,arr,n in _arrays:
        if n==0: expected=arr
        elif ident.endswith('07'): expected=list(reversed(arr))
        elif 'INT_MAX' in arr: expected=['INT_MIN',0,'INT_MAX']
        else: expected=sorted(arr)
        branches.append((label,_array_branch(name,arr,n,expected)))
    C01_EXERCISES[ident]=_spec(name,'void','int *, int',branches)

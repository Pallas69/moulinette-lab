"""C 12 v9.0 : listes chaînées, contrats pédagogiques non officiels."""
from .c01_catalog import _condition_harness, _prototype
from .project_catalog import project_spec

_LIST_H='''#ifndef FT_LIST_H
#define FT_LIST_H
typedef struct s_list { struct s_list *next; void *data; } t_list;
#endif
'''
_SUPPORT='''#include <stdlib.h>
#include "ft_list.h"
t_list *ft_create_elem(void *data) { t_list *p=malloc(sizeof *p); if(p){p->data=data;p->next=0;} return p; }
'''
_CMP='''
int ml_cmp(void *a,void *b) { int x=*(int *)a,y=*(int *)b; return (x>y)-(x<y); }
'''
_COLLECT='''
int ml_seen[20],ml_count;
void ml_collect(void *x) { if(ml_count<20)ml_seen[ml_count++]=*(int *)x; }
'''
# The callback can be observed without freeing stack-backed data.
_FREE='''
int ml_freed; void *ml_free_seen[20];
void ml_release(void *x) { if(ml_freed<20)ml_free_seen[ml_freed]=x;ml_freed++; }
'''
C12_EXERCISES={}
def add(i,name,ret,params,branches,*,helper='',allowed=(),uses_create=False):
 src=name+'.c'; include='#include "ft_list.h"\n'+ret+' '+name+'('+params+');'
 harness=_condition_harness(include,branches,'#include <stdlib.h>\n'+helper)
 header_required=i!=8
 required=[src,'ft_list.h'] if header_required else [src]
 cfg={'required_files':required,'exact_files':True,'sources':[src],'build':'cc','binary':'test-list',
      'compile_standard':'c11',
      'allowed_functions':list(allowed),'support_functions':['ft_create_elem'] if uses_create else [],
      'prototype':_prototype(name,ret,params),'harness':harness,
      'cases':[{'label':l,'argv':[str(j)],'expected':b'OK','marker':True,'code':73} for j,(l,_) in enumerate(branches)],
      'style_files':required}
 if uses_create:cfg['support']=_SUPPORT
 if not header_required:cfg['provided_files']={'ft_list.h':_LIST_H}
 C12_EXERCISES[f'c12/ex{i:02}']=project_spec(src,'9.0',cfg)

add(0,'ft_create_elem','t_list *','void *',[
 ('donnée','int x=42;t_list *p=ft_create_elem(&x);int ok=p && p->data==&x && p->next==0;free(p);return ok;'),
 ('donnée nulle','t_list *p=ft_create_elem(0);int ok=p && p->data==0 && p->next==0;free(p);return ok;')],allowed=('malloc',))
add(1,'ft_list_push_front','void','t_list **, void *',[
 ('liste vide','int x=42;t_list *p=0;ft_list_push_front(&p,&x);int ok=p && p->data==&x && !p->next;free(p);return ok;'),
 ('ajout devant','int a=1,b=2;t_list n={.data=&a,.next=0},*p=&n;ft_list_push_front(&p,&b);int ok=p && p!=&n && p->data==&b && p->next==&n;if(p!=&n)free(p);return ok;')],uses_create=True)
add(2,'ft_list_size','int','t_list *',[
 ('liste vide','return ft_list_size(0)==0;'),('trois liens','int a=1,b=2,c=3;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2};return ft_list_size(&n1)==3;')])
add(3,'ft_list_last','t_list *','t_list *',[
 ('liste vide','return ft_list_last(0)==0;'),('dernier lien','int a=1,b=2;t_list n2={.data=&b,.next=0},n1={.data=&a,.next=&n2};return ft_list_last(&n1)==&n2 && ft_list_last(&n2)==&n2;')])
add(4,'ft_list_push_back','void','t_list **, void *',[
 ('liste vide','int x=42;t_list *p=0;ft_list_push_back(&p,&x);int ok=p && p->data==&x && !p->next;free(p);return ok;'),
 ('ajout en fin','int a=1,b=2;t_list n={.data=&a,.next=0},*p=&n;ft_list_push_back(&p,&b);t_list *q=n.next;int ok=p==&n && q && q->data==&b && !q->next;free(q);return ok;')],uses_create=True)
add(5,'ft_list_push_strs','t_list *','int, char **',[
 ('aucune chaîne','char *a[]={0};return ft_list_push_strs(0,a)==0;'),
 ('ordre inversé','char a[]="A",b[]="B",c[]="C",*s[]={a,b,c};t_list *p=ft_list_push_strs(3,s),*q=p;int i=0,ok=1;char *want[]={c,b,a};while(q && i<3){if(q->data!=want[i])ok=0;q=q->next;i++;}if(i!=3||q)ok=0;while(p){q=p->next;free(p);p=q;}return ok;')],uses_create=True)
add(6,'ft_list_clear','void','t_list *, void (*)(void *)',[
 ('vide','ml_freed=0;ft_list_clear(0,ml_release);return ml_freed==0 && ml_unfreed_count()==0;'),
 ('trois callbacks','int a=1,b=2,c=3;t_list *x=malloc(sizeof *x),*y=malloc(sizeof *y),*z=malloc(sizeof *z);if(!x||!y||!z)return 0;*x=(t_list){.data=&a,.next=y};*y=(t_list){.data=&b,.next=z};*z=(t_list){.data=&c,.next=0};ml_freed=0;ft_list_clear(x,ml_release);return ml_freed==3 && ml_unfreed_count()==0;'),
 ('données transmises au callback','int a=1,b=2,c=3;t_list *x=malloc(sizeof *x),*y=malloc(sizeof *y),*z=malloc(sizeof *z);int i,ca=0,cb=0,cc=0;if(!x||!y||!z)return 0;*x=(t_list){.data=&a,.next=y};*y=(t_list){.data=&b,.next=z};*z=(t_list){.data=&c,.next=0};ml_freed=0;ft_list_clear(x,ml_release);if(ml_freed!=3 || ml_unfreed_count()!=0)return 0;for(i=0;i<3;i++){ca+=ml_free_seen[i]==&a;cb+=ml_free_seen[i]==&b;cc+=ml_free_seen[i]==&c;}return ca==1 && cb==1 && cc==1;')],helper=_FREE,allowed=('free',))
add(7,'ft_list_at','t_list *','t_list *, unsigned int',[
 ('vide','return ft_list_at(0,0)==0;'),('indices','int a=1,b=2;t_list n2={.data=&b,.next=0},n1={.data=&a,.next=&n2};return ft_list_at(&n1,0)==&n1 && ft_list_at(&n1,1)==&n2 && ft_list_at(&n1,2)==0;')])
add(8,'ft_list_reverse','void','t_list **',[
 ('vide','t_list *p=0;ft_list_reverse(&p);return p==0;'),
 ('trois liens','int a=1,b=2,c=3;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2},*p=&n1;ft_list_reverse(&p);return p==&n3 && n3.next==&n2 && n2.next==&n1 && n1.next==0 && n1.data==&a && n3.data==&c;')])
add(9,'ft_list_foreach','void','t_list *, void (*)(void *)',[
 ('ordre','int a=1,b=2,c=3;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2};ml_count=0;ft_list_foreach(&n1,ml_collect);return ml_count==3 && ml_seen[0]==1 && ml_seen[1]==2 && ml_seen[2]==3;'),
 ('vide','ml_count=0;ft_list_foreach(0,ml_collect);return ml_count==0;')],helper=_COLLECT)
add(10,'ft_list_foreach_if','void','t_list *, void (*)(void *), void *, int (*)()',[
 ('sélection','int a=1,b=2,c=1,k=1;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2};ml_count=0;ft_list_foreach_if(&n1,ml_collect,&k,ml_cmp);return ml_count==2 && ml_seen[0]==1 && ml_seen[1]==1;'),
 ('aucun','int a=1,k=2;t_list n={.data=&a,.next=0};ml_count=0;ft_list_foreach_if(&n,ml_collect,&k,ml_cmp);return ml_count==0;')],helper=_COLLECT+_CMP)
add(11,'ft_list_find','t_list *','t_list *, void *, int (*)()',[
 ('première occurrence','int a=1,b=2,c=1,k=1;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2};return ft_list_find(&n1,&k,ml_cmp)==&n1;'),
 ('absence','int a=1,k=2;t_list n={.data=&a,.next=0};return ft_list_find(&n,&k,ml_cmp)==0;')],helper=_CMP)
add(12,'ft_list_remove_if','void','t_list **, void *, int (*)(), void (*)(void *)',[
 ('suppression tête et fin','int a=1,b=2,c=1,k=1;t_list *x=malloc(sizeof *x),*y=malloc(sizeof *y),*z=malloc(sizeof *z),*p=x;int ok;if(!x||!y||!z)return 0;*x=(t_list){.data=&a,.next=y};*y=(t_list){.data=&b,.next=z};*z=(t_list){.data=&c,.next=0};ml_freed=0;ft_list_remove_if(&p,&k,ml_cmp,ml_release);ok=p==y && p->data==&b && p->next==0 && ml_freed==2;if(p==y)free(y);return ok && ml_unfreed_count()==0;'),
 ('liste vide','int k=1;t_list *p=0;ml_freed=0;ft_list_remove_if(&p,&k,ml_cmp,ml_release);return !p && ml_freed==0 && ml_unfreed_count()==0;')],helper=_CMP+_FREE,allowed=('free',))
add(13,'ft_list_merge','void','t_list **, t_list *',[
 ('deux listes','int a=1,b=2;t_list n2={.data=&b,.next=0},n1={.data=&a,.next=0},*p=&n1;ft_list_merge(&p,&n2);return p==&n1 && n1.next==&n2 && !n2.next;'),
 ('première vide','int a=1;t_list n={.data=&a,.next=0},*p=0;ft_list_merge(&p,&n);return p==&n && !n.next;')])
add(14,'ft_list_sort','void','t_list **, int (*)()',[
 ('tri','int a=3,b=1,c=2;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2},*p=&n1;int i=1;ft_list_sort(&p,ml_cmp);while(p && i<=3){if(*(int *)p->data!=i)return 0;p=p->next;i++;}return i==4 && !p;'),
 ('vide','t_list *p=0;ft_list_sort(&p,ml_cmp);return p==0;')],helper=_CMP)
add(15,'ft_list_reverse_fun','void','t_list *',[
 ('inversion des données','int a=1,b=2,c=3;t_list n3={.data=&c,.next=0},n2={.data=&b,.next=&n3},n1={.data=&a,.next=&n2};ft_list_reverse_fun(&n1);return n1.data==&c && n2.data==&b && n3.data==&a && n1.next==&n2 && n2.next==&n3;'),
 ('vide','ft_list_reverse_fun(0);return 1;')])
add(16,'ft_sorted_list_insert','void','t_list **, void *, int (*)()',[
 ('insertion au milieu','int a=1,b=3,c=2;t_list n2={.data=&b,.next=0},n1={.data=&a,.next=&n2},*p=&n1,*mid;int ok;ft_sorted_list_insert(&p,&c,ml_cmp);mid=n1.next;ok=p==&n1 && mid && mid!=&n2 && mid->data==&c && mid->next==&n2;if(mid && mid!=&n2)free(mid);return ok;'),
 ('liste vide','int a=1;t_list *p=0;ft_sorted_list_insert(&p,&a,ml_cmp);int ok=p && p->data==&a && !p->next;free(p);return ok;')],helper=_CMP,uses_create=True)
add(17,'ft_sorted_list_merge','void','t_list **, t_list *, int (*)()',[
 ('fusion','int a=1,b=3,c=2,d=4;t_list n2={.data=&b,.next=0},n1={.data=&a,.next=&n2},n4={.data=&d,.next=0},n3={.data=&c,.next=&n4},*p=&n1;int i=1;ft_sorted_list_merge(&p,&n3,ml_cmp);while(p && i<=4){if(*(int *)p->data!=i)return 0;p=p->next;i++;}return i==5 && !p;'),
 ('première vide','int a=1;t_list n={.data=&a,.next=0},*p=0;ft_sorted_list_merge(&p,&n,ml_cmp);return p==&n && !n.next;')],helper=_CMP)

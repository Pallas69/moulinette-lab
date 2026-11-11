"""C 13 v6 : arbres binaires, tests locaux non officiels."""
from .c01_catalog import _condition_harness, _prototype
from .project_catalog import project_spec
_SUPPORT='''#include <stdlib.h>
#include "ft_btree.h"
t_btree *btree_create_node(void *data) { t_btree *p=malloc(sizeof *p);if(p){p->item=data;p->left=0;p->right=0;}return p; }
'''
_CMP='int ml_cmp(void *a,void *b) { int x=*(int *)a,y=*(int *)b;return (x>y)-(x<y); }\n'
_VISIT='''
int ml_seen[32],ml_count;
void ml_visit(void *p) { if(ml_count<32)ml_seen[ml_count++]=*(int *)p; }
'''
C13_EXERCISES={}
def add(i,name,ret,params,branches,*,helper='',allowed=(),uses_create=False):
 src=name+'.c';decl='#include "ft_btree.h"\n'+ret+' '+name+'('+params+');'
 h=_condition_harness(decl,branches,'#include <stdlib.h>\n'+helper)
 cfg={'required_files':[src,'ft_btree.h'],'exact_files':True,'sources':[src],'build':'cc','binary':'test-tree',
      'allowed_functions':list(allowed),'support_functions':['btree_create_node'] if uses_create else [],
      'prototype':_prototype(name,ret,params),'harness':h,
      'cases':[{'label':l,'argv':[str(j)],'expected':b'OK','marker':True,'code':73} for j,(l,_) in enumerate(branches)],
      'style_files':[src,'ft_btree.h']}
 if uses_create:cfg['support']=_SUPPORT
 C13_EXERCISES[f'c13/ex{i:02}']=project_spec(src,'6.0',cfg)

add(0,'btree_create_node','t_btree *','void *',[
 ('donnée','int a=7;t_btree *p=btree_create_node(&a);int ok=p && p->item==&a && !p->left && !p->right;free(p);return ok;'),
 ('donnée nulle','t_btree *p=btree_create_node(0);int ok=p && !p->item && !p->left && !p->right;free(p);return ok;')],allowed=('malloc',))
for i,name,order in [(1,'btree_apply_prefix',[1,2,4,3,5]),(2,'btree_apply_infix',[4,2,1,3,5]),(3,'btree_apply_suffix',[4,2,5,3,1])]:
 test='int a=1,b=2,c=3,d=4,e=5;t_btree n4={.item=&d},n5={.item=&e},n2={.item=&b,.left=&n4},n3={.item=&c,.right=&n5},n1={.item=&a,.left=&n2,.right=&n3};ml_count=0;'+name+'(&n1,ml_visit);return ml_count==5 && '+' && '.join(f'ml_seen[{j}]=={v}' for j,v in enumerate(order))+';'
 add(i,name,'void','t_btree *, void (*)(void *)',[('parcours et ordre',test),('arbre vide',f'ml_count=0;{name}(0,ml_visit);return ml_count==0;')],helper=_VISIT)
add(4,'btree_insert_data','void','t_btree **, void *, int (*)(void *, void *)',[
 ('insertion et égalité','int a=4,b=2,c=6,d=4,ok;t_btree *p=0;btree_insert_data(&p,&a,ml_cmp);btree_insert_data(&p,&b,ml_cmp);btree_insert_data(&p,&c,ml_cmp);btree_insert_data(&p,&d,ml_cmp);ok=p && p->item==&a && p->left && p->left->item==&b && p->right && p->right->item==&c && p->right->left && p->right->left->item==&d;if(ok){free(p->left);free(p->right->left);free(p->right);free(p);}return ok;')],helper=_CMP,uses_create=True)
add(5,'btree_search_item','void *','t_btree *, void *, int (*)(void *, void *)',[
 ('infixe même arbre non trié','int a=5,b=8,c=2,k=2;t_btree n2={.item=&b},n3={.item=&c},n1={.item=&a,.left=&n2,.right=&n3};return btree_search_item(&n1,&k,ml_cmp)==&c;'),
 ('première occurrence infixe','int a=1,b=1,k=1;t_btree n2={.item=&b},n1={.item=&a,.left=&n2};return btree_search_item(&n1,&k,ml_cmp)==&b;'),
 ('arbre vide','int k=1;return btree_search_item(0,&k,ml_cmp)==0;'),
 ('élément absent dans arbre non vide','int a=1,b=3,k=2;t_btree right={.item=&b},root={.item=&a,.right=&right};return btree_search_item(&root,&k,ml_cmp)==0;')],helper=_CMP)
add(6,'btree_level_count','int','t_btree *',[
 ('arbre vide','return btree_level_count(0)==0;'),('une branche','int a=1,b=2,c=3;t_btree n3={.item=&c},n2={.item=&b,.left=&n3},n1={.item=&a,.left=&n2};return btree_level_count(&n1)==3 && btree_level_count(&n3)==1;'),
 ('branche droite plus longue','int a=1,b=2,c=3,d=4;t_btree leaf={.item=&d},right={.item=&c,.right=&leaf},left={.item=&b},root={.item=&a,.left=&left,.right=&right};return btree_level_count(&root)==3;')])
_LEVEL='''
int ml_values[16],ml_levels[16],ml_first[16],ml_count;
void ml_level(void *p,int level,int first) {if(ml_count<16){ml_values[ml_count]=*(int *)p;ml_levels[ml_count]=level;ml_first[ml_count]=first;ml_count++;}}
'''
add(7,'btree_apply_by_level','void','t_btree *, void (*)(void *, int, int)',[
 ('niveaux et premier élément','int a=1,b=2,c=3,d=4,e=5;t_btree n4={.item=&d},n5={.item=&e},n2={.item=&b,.right=&n4},n3={.item=&c,.left=&n5},n1={.item=&a,.left=&n2,.right=&n3};int i,levels[]={0,1,1,2,2},first[]={1,1,0,1,0};ml_count=0;btree_apply_by_level(&n1,ml_level);if(ml_count!=5)return 0;for(i=0;i<5;i++)if(ml_values[i]!=i+1 || ml_levels[i]!=levels[i] || ml_first[i]!=first[i])return 0;return 1;'),
 ('arbre vide','ml_count=0;btree_apply_by_level(0,ml_level);return ml_count==0;')],helper=_LEVEL,allowed=('malloc','free'))

#include "ft_btree.h"

void	btree_apply_infix(t_btree *p, void (*f)(void *))
{
	if (!p)
		return ;
	btree_apply_infix(p->left, f);
	f(p->item);
	btree_apply_infix(p->right, f);
}

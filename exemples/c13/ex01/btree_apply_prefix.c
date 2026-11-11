#include "ft_btree.h"

void	btree_apply_prefix(t_btree *p, void (*f)(void *))
{
	if (!p)
		return ;
	f(p->item);
	btree_apply_prefix(p->left, f);
	btree_apply_prefix(p->right, f);
}

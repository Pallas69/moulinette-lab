#include "ft_btree.h"

void	btree_apply_suffix(t_btree *p, void (*f)(void *))
{
	if (!p)
		return ;
	btree_apply_suffix(p->left, f);
	btree_apply_suffix(p->right, f);
	f(p->item);
}

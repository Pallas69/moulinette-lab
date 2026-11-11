#include "ft_btree.h"

void	btree_insert_data(t_btree **p, void *d, int (*cmp)(void *, void *))
{
	while (*p)
	{
		if (cmp(d, (*p)->item) < 0)
			p = &(*p)->left;
		else
			p = &(*p)->right;
	}
	*p = btree_create_node(d);
}

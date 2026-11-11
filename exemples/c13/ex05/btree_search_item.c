#include "ft_btree.h"

void	*btree_search_item(t_btree *p, void *d, int (*cmp)(void *, void *))
{
	void	*v;

	if (!p)
		return (0);
	v = btree_search_item(p->left, d, cmp);
	if (v)
		return (v);
	if (!cmp(p->item, d))
		return (p->item);
	return (btree_search_item(p->right, d, cmp));
}

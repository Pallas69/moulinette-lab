#include "ft_btree.h"

int	btree_level_count(t_btree *p)
{
	int	a;
	int	b;

	if (!p)
		return (0);
	a = btree_level_count(p->left);
	b = btree_level_count(p->right);
	if (a > b)
		return (a + 1);
	return (b + 1);
}

#include "ft_btree.h"
#include <stdlib.h>

t_btree	*btree_create_node(void *d)
{
	t_btree	*p;

	p = malloc(sizeof(*p));
	if (p)
	{
		p->item = d;
		p->left = 0;
		p->right = 0;
	}
	return (p);
}

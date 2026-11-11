#include "ft_list.h"

void	ft_sorted_list_insert(t_list **p, void *d, int (*cmp)())
{
	t_list	*n;

	n = ft_create_elem(d);
	if (!n)
		return ;
	while (*p && cmp((*p)->data, d) < 0)
		p = &(*p)->next;
	n->next = *p;
	*p = n;
}

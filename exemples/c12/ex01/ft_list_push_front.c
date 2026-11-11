#include "ft_list.h"

void	ft_list_push_front(t_list **p, void *d)
{
	t_list	*n;

	n = ft_create_elem(d);
	if (n)
	{
		n->next = *p;
		*p = n;
	}
}

#include "ft_list.h"

void	ft_list_push_back(t_list **p, void *d)
{
	t_list	*n;
	t_list	*q;

	n = ft_create_elem(d);
	q = *p;
	if (!n)
		return ;
	if (!q)
	{
		*p = n;
		return ;
	}
	while (q->next)
		q = q->next;
	q->next = n;
}

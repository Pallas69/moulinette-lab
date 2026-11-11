#include "ft_list.h"

void	ft_sorted_list_merge(t_list **p, t_list *q, int (*cmp)())
{
	t_list	*n;

	while (q)
	{
		n = q->next;
		while (*p && cmp((*p)->data, q->data) <= 0)
			p = &(*p)->next;
		q->next = *p;
		*p = q;
		q = n;
	}
}

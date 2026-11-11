#include "ft_list.h"

void	ft_list_reverse(t_list **p)
{
	t_list	*q;
	t_list	*n;
	t_list	*a;

	q = 0;
	a = *p;
	while (a)
	{
		n = a->next;
		a->next = q;
		q = a;
		a = n;
	}
	*p = q;
}

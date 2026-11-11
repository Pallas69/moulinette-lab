#include "ft_list.h"

void	ft_list_sort(t_list **p, int (*cmp)())
{
	t_list	*a;
	t_list	*b;
	void	*t;

	a = *p;
	while (a)
	{
		b = a->next;
		while (b)
		{
			if (cmp(a->data, b->data) > 0)
			{
				t = a->data;
				a->data = b->data;
				b->data = t;
			}
			b = b->next;
		}
		a = a->next;
	}
}

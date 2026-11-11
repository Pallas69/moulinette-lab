#include "ft_list.h"

void	ft_list_foreach_if(t_list *p, void (*f)(void *), void *r, int (*cmp)())
{
	while (p)
	{
		if (!cmp(p->data, r))
			f(p->data);
		p = p->next;
	}
}

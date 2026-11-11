#include "ft_list.h"
#include <stdlib.h>

void	ft_list_remove_if(t_list **p, void *r, int (*cmp)(), void (*f)(void *))
{
	t_list	*n;

	while (*p)
	{
		if (!cmp((*p)->data, r))
		{
			n = *p;
			*p = n->next;
			f(n->data);
			free(n);
		}
		else
			p = &(*p)->next;
	}
}

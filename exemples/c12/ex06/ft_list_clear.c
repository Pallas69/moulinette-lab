#include "ft_list.h"
#include <stdlib.h>

void	ft_list_clear(t_list *p, void (*f)(void *))
{
	t_list	*n;

	while (p)
	{
		n = p->next;
		f(p->data);
		free(p);
		p = n;
	}
}

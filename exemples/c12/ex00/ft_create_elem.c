#include "ft_list.h"
#include <stdlib.h>

t_list	*ft_create_elem(void *d)
{
	t_list	*p;

	p = malloc(sizeof(*p));
	if (p)
	{
		p->data = d;
		p->next = 0;
	}
	return (p);
}

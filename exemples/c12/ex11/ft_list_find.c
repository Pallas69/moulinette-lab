#include "ft_list.h"

t_list	*ft_list_find(t_list *p, void *r, int (*cmp)())
{
	while (p)
	{
		if (!cmp(p->data, r))
			return (p);
		p = p->next;
	}
	return (0);
}

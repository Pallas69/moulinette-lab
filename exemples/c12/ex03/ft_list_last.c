#include "ft_list.h"

t_list	*ft_list_last(t_list *p)
{
	if (!p)
		return (0);
	while (p->next)
		p = p->next;
	return (p);
}

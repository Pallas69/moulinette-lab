#include "ft_list.h"

t_list	*ft_list_at(t_list *p, unsigned int n)
{
	while (p && n-- > 0)
		p = p->next;
	return (p);
}

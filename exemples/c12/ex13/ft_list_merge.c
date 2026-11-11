#include "ft_list.h"

void	ft_list_merge(t_list **p, t_list *b)
{
	if (!*p)
	{
		*p = b;
		return ;
	}
	while ((*p)->next)
		p = &(*p)->next;
	(*p)->next = b;
}

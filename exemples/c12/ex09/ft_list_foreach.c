#include "ft_list.h"

void	ft_list_foreach(t_list *p, void (*f)(void *))
{
	while (p)
	{
		f(p->data);
		p = p->next;
	}
}

#include "ft_list.h"

int	ft_list_size(t_list *p)
{
	int	n;

	n = 0;
	while (p)
	{
		n++;
		p = p->next;
	}
	return (n);
}

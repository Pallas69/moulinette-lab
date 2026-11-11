#include "ft_list.h"

t_list	*ft_list_push_strs(int n, char **s)
{
	int		i;
	t_list	*p;
	t_list	*q;

	i = 0;
	p = 0;
	while (i < n)
	{
		q = ft_create_elem(s[i]);
		i++;
		if (!q)
			return (p);
		q->next = p;
		p = q;
	}
	return (p);
}

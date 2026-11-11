#include "ft_list.h"

static int	len(t_list *p)
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

static t_list	*at(t_list *p, int n)
{
	while (n > 0)
	{
		p = p->next;
		n--;
	}
	return (p);
}

void	ft_list_reverse_fun(t_list *p)
{
	int		i;
	int		n;
	t_list	*a;
	t_list	*b;
	void	*x;

	i = 0;
	n = len(p);
	while (i < n / 2)
	{
		a = at(p, i);
		b = at(p, n - 1 - i);
		x = a->data;
		a->data = b->data;
		b->data = x;
		i++;
	}
}

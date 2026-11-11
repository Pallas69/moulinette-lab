#include "ft_btree.h"

static void	level(t_btree *p, int depth, int current, t_state *s)
{
	if (!p)
		return ;
	if (depth == 0)
	{
		s->f(p->item, current, s->first);
		s->first = 0;
		return ;
	}
	level(p->left, depth - 1, current, s);
	level(p->right, depth - 1, current, s);
}

static int	depth(t_btree *p)
{
	int	a;
	int	b;

	if (!p)
		return (0);
	a = depth(p->left);
	b = depth(p->right);
	if (a > b)
		return (a + 1);
	return (b + 1);
}

void	btree_apply_by_level(t_btree *p, void (*f)(void *, int, int))
{
	int		i;
	int		n;
	t_state	s;

	i = 0;
	n = depth(p);
	s.f = f;
	while (i < n)
	{
		s.first = 1;
		level(p, i, i, &s);
		i++;
	}
}

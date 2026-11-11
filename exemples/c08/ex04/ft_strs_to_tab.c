#include <stdlib.h>
#include "ft_stock_str.h"

static int	ft_length(char *s)
{
	int	i;

	i = 0;
	while (s[i])
		i++;
	return (i);
}

static char	*ft_copy(char *s)
{
	int		i;
	char	*p;

	p = malloc(ft_length(s) + 1);
	if (!p)
		return (0);
	i = 0;
	while (s[i])
	{
		p[i] = s[i];
		i++;
	}
	p[i] = 0;
	return (p);
}

static void	clear_tab(t_stock_str *tab, int i)
{
	while (i > 0)
		free(tab[--i].copy);
	free(tab);
}

struct s_stock_str	*ft_strs_to_tab(int ac, char **av)
{
	t_stock_str	*tab;
	int			i;

	tab = malloc(sizeof(t_stock_str) * (ac + 1));
	if (!tab)
		return (0);
	i = 0;
	while (i < ac)
	{
		tab[i].size = ft_length(av[i]);
		tab[i].str = av[i];
		tab[i].copy = ft_copy(av[i]);
		if (!tab[i].copy)
		{
			clear_tab(tab, i);
			return (0);
		}
		i++;
	}
	tab[i].str = 0;
	return (tab);
}

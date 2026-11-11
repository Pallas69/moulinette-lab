#include <unistd.h>
#include "ft_stock_str.h"

static void	putstr(char *s)
{
	while (*s)
		write(1, s++, 1);
	write(1, "\n", 1);
}

static void	putnbr(int n)
{
	char	c;

	if (n >= 10)
		putnbr(n / 10);
	c = '0' + n % 10;
	write(1, &c, 1);
}

void	ft_show_tab(struct s_stock_str *par)
{
	int	i;

	i = 0;
	while (par[i].str)
	{
		putstr(par[i].str);
		putnbr(par[i].size);
		write(1, "\n", 1);
		putstr(par[i].copy);
		i++;
	}
}

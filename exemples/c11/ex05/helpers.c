#include <unistd.h>
#include "do_op.h"

int	ft_number(char *s)
{
	int	n;
	int	sign;

	n = 0;
	sign = 1;
	while (*s == ' ' || (*s >= 9 && *s <= 13))
		s++;
	while (*s == '+' || *s == '-')
	{
		if (*s == '-')
			sign = -sign;
		s++;
	}
	while (*s >= '0' && *s <= '9')
	{
		n = n * 10 + (*s - '0');
		s++;
	}
	return (n * sign);
}

void	ft_number_out(long n)
{
	char	c;

	if (n < 0)
	{
		write(1, "-", 1);
		n = -n;
	}
	if (n >= 10)
		ft_number_out(n / 10);
	c = '0' + n % 10;
	write(1, &c, 1);
}

void	ft_text(char *s)
{
	while (*s)
		write(1, s++, 1);
}

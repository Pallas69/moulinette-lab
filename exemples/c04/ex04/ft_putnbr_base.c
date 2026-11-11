#include <unistd.h>

static int	valid(char *b)
{
	int	i;
	int	j;

	i = 0;
	while (b[i])
	{
		if (b[i] == '+' || b[i] == '-')
			return (0);
		j = 0;
		while (j < i)
		{
			if (b[i] == b[j])
				return (0);
			j++;
		}
		i++;
	}
	if (i < 2)
		return (0);
	return (i);
}

static void	emit(unsigned long n, char *b, unsigned int len)
{
	if (n >= len)
		emit(n / len, b, len);
	write(1, b + n % len, 1);
}

void	ft_putnbr_base(int n, char *b)
{
	int		l;
	long	x;

	l = valid(b);
	x = n;
	if (!l)
		return ;
	if (x < 0)
	{
		write(1, "-", 1);
		x = -x;
	}
	emit((unsigned long)x, b, (unsigned int)l);
}

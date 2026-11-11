#include <unistd.h>

static void	print_pair(int a, int b)
{
	char	pair[5];

	pair[0] = '0' + a / 10;
	pair[1] = '0' + a % 10;
	pair[2] = ' ';
	pair[3] = '0' + b / 10;
	pair[4] = '0' + b % 10;
	write(1, pair, 5);
	if (a != 98 || b != 99)
		write(1, ", ", 2);
}

void	ft_print_comb2(void)
{
	int	a;
	int	b;

	a = 0;
	while (a < 99)
	{
		b = a + 1;
		while (b < 100)
			print_pair(a, b++);
		a++;
	}
}

#include <unistd.h>

static void	print_unsigned(unsigned int n)
{
	char	digit;

	if (n >= 10)
		print_unsigned(n / 10);
	digit = '0' + n % 10;
	write(1, &digit, 1);
}

void	ft_putnbr(int n)
{
	unsigned int	value;

	if (n < 0)
	{
		write(1, "-", 1);
		value = -(n + 1);
		value++;
	}
	else
		value = n;
	print_unsigned(value);
}

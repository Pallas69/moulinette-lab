#include <unistd.h>

static void	print_digits(char a, char b, char c)
{
	char	digits[3];

	digits[0] = a;
	digits[1] = b;
	digits[2] = c;
	write(1, digits, 3);
	if (a != '7' || b != '8' || c != '9')
		write(1, ", ", 2);
}

void	ft_print_comb(void)
{
	char	a;
	char	b;
	char	c;

	a = '0';
	while (a <= '7')
	{
		b = a + 1;
		while (b <= '8')
		{
			c = b + 1;
			while (c <= '9')
				print_digits(a, b, c++);
			b++;
		}
		a++;
	}
}

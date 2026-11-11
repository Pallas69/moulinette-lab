#include <unistd.h>

static void	print_combinations(char *digits, int n, int pos, int start)
{
	int	digit;

	if (pos == n)
	{
		write(1, digits, n);
		if (digits[0] != '0' + 10 - n)
			write(1, ", ", 2);
		return ;
	}
	digit = start;
	while (digit <= 10 - (n - pos))
	{
		digits[pos] = '0' + digit;
		print_combinations(digits, n, pos + 1, digit + 1);
		digit++;
	}
}

void	ft_print_combn(int n)
{
	char	digits[10];

	print_combinations(digits, n, 0, 0);
}

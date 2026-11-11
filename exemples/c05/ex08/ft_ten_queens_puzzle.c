#include <unistd.h>

static int	safe(char *q, int col, int row)
{
	int	j;

	j = 0;
	while (j < col)
	{
		if (q[j] == '0' + row || q[j] - '0' - row == col - j || row - (q[j]
				- '0') == col - j)
			return (0);
		j++;
	}
	return (1);
}

static int	solve(char *q, int col)
{
	int	row;
	int	count;

	row = 0;
	count = 0;
	if (col == 10)
	{
		q[10] = '\n';
		write(1, q, 11);
		return (1);
	}
	while (row < 10)
	{
		if (safe(q, col, row))
		{
			q[col] = '0' + row;
			count += solve(q, col + 1);
		}
		row++;
	}
	return (count);
}

int	ft_ten_queens_puzzle(void)
{
	char	q[11];

	return (solve(q, 0));
}

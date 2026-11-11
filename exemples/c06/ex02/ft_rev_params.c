#include <unistd.h>

int	main(int n, char **v)
{
	int	j;

	while (--n > 0)
	{
		j = 0;
		while (v[n][j])
			j++;
		write(1, v[n], j);
		write(1, "\n", 1);
	}
	return (0);
}

#include <unistd.h>

int	main(int n, char **v)
{
	int	i;
	int	j;

	i = 1;
	while (i < n)
	{
		j = 0;
		while (v[i][j])
			j++;
		write(1, v[i], j);
		write(1, "\n", 1);
		i++;
	}
	return (0);
}

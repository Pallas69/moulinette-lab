#include <unistd.h>

int	main(int n, char **v)
{
	int	i;

	i = 0;
	(void)n;
	while (v[0][i])
		i++;
	write(1, v[0], i);
	write(1, "\n", 1);
	return (0);
}

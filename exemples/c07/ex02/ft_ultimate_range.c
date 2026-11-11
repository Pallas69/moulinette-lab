#include <stdlib.h>

int	ft_ultimate_range(int **p, int min, int max)
{
	int	i;
	int	n;

	i = 0;
	if (min >= max)
	{
		*p = 0;
		return (0);
	}
	n = max - min;
	*p = malloc(sizeof(int) * n);
	if (!*p)
		return (-1);
	while (i < n)
	{
		(*p)[i] = min + i;
		i++;
	}
	return (n);
}

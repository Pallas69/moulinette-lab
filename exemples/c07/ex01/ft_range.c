#include <stdlib.h>

int	*ft_range(int min, int max)
{
	int	*p;
	int	i;

	i = 0;
	if (min >= max)
		return (0);
	p = malloc(sizeof(int) * (max - min));
	if (!p)
		return (0);
	while (min < max)
	{
		p[i] = min;
		i++;
		min++;
	}
	return (p);
}

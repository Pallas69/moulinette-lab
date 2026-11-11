#include <stdlib.h>

int	*ft_map(int *a, int n, int (*f)(int))
{
	int	i;
	int	*p;

	p = malloc(sizeof(int) * n);
	if (!p)
		return (0);
	i = 0;
	while (i < n)
	{
		p[i] = f(a[i]);
		i++;
	}
	return (p);
}

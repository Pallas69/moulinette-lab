#include <stdlib.h>

static int	len(char *s)
{
	int	i;

	i = 0;
	while (s[i])
		i++;
	return (i);
}

static int	total(int n, char **s, char *sep)
{
	int	i;
	int	size;

	i = 0;
	size = 0;
	while (i < n)
	{
		size += len(s[i]);
		if (i)
			size += len(sep);
		i++;
	}
	return (size);
}

static int	copy(char *out, char *s, int k)
{
	int	j;

	j = 0;
	while (s[j])
	{
		out[k] = s[j];
		k++;
		j++;
	}
	return (k);
}

char	*ft_strjoin(int n, char **s, char *sep)
{
	int		i;
	int		k;
	char	*p;

	p = malloc(total(n, s, sep) + 1);
	if (!p)
		return (0);
	i = 0;
	k = 0;
	while (i < n)
	{
		if (i)
			k = copy(p, sep, k);
		k = copy(p, s[i], k);
		i++;
	}
	p[k] = 0;
	return (p);
}

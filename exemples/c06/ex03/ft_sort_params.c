#include <unistd.h>

static int	cmp(char *a, char *b)
{
	while (*a && *a == *b)
	{
		a++;
		b++;
	}
	return ((unsigned char)*a - (unsigned char)*b);
}

static void	sort(int n, char **v)
{
	int		i;
	int		j;
	char	*t;

	i = 1;
	while (i < n)
	{
		j = i + 1;
		while (j < n)
		{
			if (cmp(v[i], v[j]) > 0)
			{
				t = v[i];
				v[i] = v[j];
				v[j] = t;
			}
			j++;
		}
		i++;
	}
}

int	main(int n, char **v)
{
	int	i;
	int	k;

	sort(n, v);
	i = 1;
	while (i < n)
	{
		k = 0;
		while (v[i][k])
			k++;
		write(1, v[i], k);
		write(1, "\n", 1);
		i++;
	}
	return (0);
}

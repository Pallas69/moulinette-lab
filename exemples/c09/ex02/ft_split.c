#include <stdlib.h>

static int	isin(char c, char *set)
{
	int	i;

	i = 0;
	while (set[i])
	{
		if (c == set[i])
			return (1);
		i++;
	}
	return (0);
}

static int	count(char *s, char *set)
{
	int	i;
	int	n;

	i = 0;
	n = 0;
	while (s[i])
	{
		while (s[i] && isin(s[i], set))
			i++;
		if (s[i])
		{
			n++;
			while (s[i] && !isin(s[i], set))
				i++;
		}
	}
	return (n);
}

static char	*word(char *s, int len)
{
	int		j;
	char	*p;

	p = malloc(len + 1);
	if (!p)
		return (0);
	j = 0;
	while (j < len)
	{
		p[j] = s[j];
		j++;
	}
	p[j] = 0;
	return (p);
}

static int	word_len(char *s, char *set)
{
	int	i;

	i = 0;
	while (s[i] && !isin(s[i], set))
		i++;
	return (i);
}

char	**ft_split(char *s, char *set)
{
	int		i;
	int		n;
	int		k;
	int		l;
	char	**p;

	n = count(s, set);
	p = malloc(sizeof(char *) * (n + 1));
	if (!p)
		return (0);
	i = 0;
	k = 0;
	while (k < n)
	{
		while (s[i] && isin(s[i], set))
			i++;
		l = word_len(s + i, set);
		p[k] = word(s + i, l);
		if (!p[k])
			return (0);
		i += l;
		k++;
	}
	p[k] = 0;
	return (p);
}

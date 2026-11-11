int	base_size(char *base)
{
	int	i;
	int	j;

	i = 0;
	while (base[i])
	{
		if (base[i] == '+' || base[i] == '-' || base[i] == ' '
			|| (base[i] >= 9 && base[i] <= 13))
			return (0);
		j = 0;
		while (j < i)
		{
			if (base[i] == base[j])
				return (0);
			j++;
		}
		i++;
	}
	if (i < 2)
		return (0);
	return (i);
}

long	read_base(char *s, char *base, int len)
{
	long	n;
	int		sign;
	int		j;

	n = 0;
	sign = 1;
	while (*s == ' ' || (*s >= 9 && *s <= 13))
		s++;
	while (*s == '+' || *s == '-')
	{
		if (*s++ == '-')
			sign = -sign;
	}
	while (*s)
	{
		j = 0;
		while (j < len && base[j] != *s)
			j++;
		if (j == len)
			break ;
		n = n * len + j;
		s++;
	}
	return (n * sign);
}

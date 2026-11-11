static int	check(char *b)
{
	int	i;
	int	j;

	i = 0;
	while (b[i])
	{
		if (b[i] == '+' || b[i] == '-' || b[i] == ' ' || (b[i] >= 9
				&& b[i] <= 13))
			return (0);
		j = 0;
		while (j < i)
		{
			if (b[i] == b[j])
				return (0);
			j++;
		}
		i++;
	}
	if (i < 2)
		return (0);
	return (i);
}

static int	sign_and_skip(char **str)
{
	int	sign;

	sign = 1;
	while (**str == ' ' || (**str >= 9 && **str <= 13))
		(*str)++;
	while (**str == '+' || **str == '-')
	{
		if (**str == '-')
			sign = -sign;
		(*str)++;
	}
	return (sign);
}

int	ft_atoi_base(char *s, char *b)
{
	int	n;
	int	sign;
	int	v;
	int	l;

	l = check(b);
	if (!l)
		return (0);
	sign = sign_and_skip(&s);
	n = 0;
	while (*s)
	{
		v = 0;
		while (v < l && b[v] != *s)
			v++;
		if (v == l)
			break ;
		n = n * l + v;
		s++;
	}
	return (sign * n);
}

int	ft_atoi(char *s)
{
	int	i;
	int	sign;
	int	n;

	i = 0;
	sign = 1;
	n = 0;
	while (s[i] == ' ' || (s[i] >= 9 && s[i] <= 13))
		i++;
	while (s[i] == '+' || s[i] == '-')
	{
		if (s[i] == '-')
			sign = -sign;
		i++;
	}
	while (s[i] >= '0' && s[i] <= '9')
	{
		n = n * 10 + s[i] - '0';
		i++;
	}
	return (n * sign);
}

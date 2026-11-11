int	ft_sqrt(int n)
{
	int	i;

	i = 1;
	if (n <= 0)
		return (0);
	while (i <= n / i)
	{
		if (i * i == n)
			return (i);
		i++;
	}
	return (0);
}

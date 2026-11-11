static int	prime(int n)
{
	int	i;

	i = 2;
	if (n < 2)
		return (0);
	while (i <= n / i)
	{
		if (n % i == 0)
			return (0);
		i++;
	}
	return (1);
}

int	ft_find_next_prime(int n)
{
	if (n < 2)
		n = 2;
	while (!prime(n))
		n++;
	return (n);
}

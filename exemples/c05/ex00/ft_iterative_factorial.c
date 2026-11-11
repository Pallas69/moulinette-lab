int	ft_iterative_factorial(int n)
{
	int	p;
	int	i;

	p = 1;
	i = 1;
	if (n < 0)
		return (0);
	while (i <= n)
	{
		p *= i;
		i++;
	}
	return (p);
}

int	ft_recursive_power(int n, int p)
{
	if (p < 0)
		return (0);
	if (p == 0)
		return (1);
	return (n * ft_recursive_power(n, p - 1));
}

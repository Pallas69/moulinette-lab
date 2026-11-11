int	ft_recursive_factorial(int n)
{
	if (n < 0)
		return (0);
	if (n < 2)
		return (1);
	return (n * ft_recursive_factorial(n - 1));
}

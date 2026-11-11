int	ft_fibonacci(int n)
{
	if (n < 0)
		return (-1);
	if (n < 2)
		return (n);
	return (ft_fibonacci(n - 1) + ft_fibonacci(n - 2));
}

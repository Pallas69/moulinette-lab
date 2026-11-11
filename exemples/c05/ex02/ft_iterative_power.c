int	ft_iterative_power(int n, int p)
{
	int	r;

	r = 1;
	if (p < 0)
		return (0);
	while (p-- > 0)
		r *= n;
	return (r);
}

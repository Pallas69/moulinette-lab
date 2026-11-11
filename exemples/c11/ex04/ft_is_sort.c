int	ft_is_sort(int *a, int n, int (*f)(int, int))
{
	int	i;
	int	up;
	int	down;

	i = 1;
	up = 1;
	down = 1;
	while (i < n)
	{
		if (f(a[i - 1], a[i]) > 0)
			up = 0;
		if (f(a[i - 1], a[i]) < 0)
			down = 0;
		i++;
	}
	return (up || down);
}

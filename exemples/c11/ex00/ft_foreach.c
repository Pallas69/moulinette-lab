void	ft_foreach(int *a, int n, void (*f)(int))
{
	int	i;

	i = 0;
	while (i < n)
	{
		f(a[i]);
		i++;
	}
}

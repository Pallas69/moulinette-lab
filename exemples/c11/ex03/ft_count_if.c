int	ft_count_if(char **a, int n, int (*f)(char *))
{
	int	i;
	int	k;

	i = 0;
	k = 0;
	while (i < n)
	{
		if (f(a[i]))
			k++;
		i++;
	}
	return (k);
}

int	ft_any(char **a, int (*f)(char *))
{
	int	i;

	i = 0;
	while (a[i])
	{
		if (f(a[i]))
			return (1);
		i++;
	}
	return (0);
}

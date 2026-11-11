void	ft_advanced_sort_string_tab(char **a, int (*cmp)(char *, char *))
{
	int		i;
	int		j;
	char	*t;

	i = 0;
	while (a[i])
	{
		j = i + 1;
		while (a[j])
		{
			if (cmp(a[i], a[j]) > 0)
			{
				t = a[i];
				a[i] = a[j];
				a[j] = t;
			}
			j++;
		}
		i++;
	}
}

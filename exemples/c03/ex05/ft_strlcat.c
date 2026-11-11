unsigned int	ft_strlcat(char *d, char *s, unsigned int n)
{
	unsigned int	i;
	unsigned int	j;
	unsigned int	l;

	i = 0;
	j = 0;
	l = 0;
	while (i < n && d[i])
		i++;
	while (s[l])
		l++;
	if (i < n)
	{
		while (j < l && i + j + 1 < n)
		{
			d[i + j] = s[j];
			j++;
		}
		d[i + j] = 0;
	}
	return (i + l);
}

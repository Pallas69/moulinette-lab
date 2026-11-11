char	*ft_strncat(char *d, char *s, unsigned int n)
{
	unsigned int	i;
	unsigned int	j;

	i = 0;
	j = 0;
	while (d[i])
		i++;
	while (j < n && s[j])
	{
		d[i] = s[j];
		i++;
		j++;
	}
	d[i] = 0;
	return (d);
}

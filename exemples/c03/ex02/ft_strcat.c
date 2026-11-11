char	*ft_strcat(char *d, char *s)
{
	unsigned int	i;
	unsigned int	j;

	i = 0;
	j = 0;
	while (d[i])
		i++;
	while (s[j])
	{
		d[i] = s[j];
		i++;
		j++;
	}
	d[i] = 0;
	return (d);
}

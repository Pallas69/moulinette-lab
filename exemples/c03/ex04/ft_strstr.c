char	*ft_strstr(char *s, char *p)
{
	unsigned int	i;
	unsigned int	j;

	if (!*p)
		return (s);
	i = 0;
	while (s[i])
	{
		j = 0;
		while (s[i + j] && p[j] && s[i + j] == p[j])
			j++;
		if (!p[j])
			return (s + i);
		i++;
	}
	return (0);
}

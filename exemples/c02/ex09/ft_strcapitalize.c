static int	is_alnum(char c)
{
	return ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
		|| (c >= '0' && c <= '9'));
}

char	*ft_strcapitalize(char *str)
{
	unsigned int	i;
	int				start;

	i = 0;
	start = 1;
	while (str[i])
	{
		if (start && str[i] >= 'a' && str[i] <= 'z')
			str[i] -= 32;
		else if (!start && str[i] >= 'A' && str[i] <= 'Z')
			str[i] += 32;
		start = !is_alnum(str[i]);
		i++;
	}
	return (str);
}

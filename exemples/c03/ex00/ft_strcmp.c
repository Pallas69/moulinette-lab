int	ft_strcmp(char *a, char *b)
{
	while (*a && *a == *b)
	{
		a++;
		b++;
	}
	return ((unsigned char)*a - (unsigned char)*b);
}

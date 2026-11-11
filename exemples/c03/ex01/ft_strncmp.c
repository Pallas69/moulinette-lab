int	ft_strncmp(char *a, char *b, unsigned int n)
{
	while (n && *a && *a == *b)
	{
		a++;
		b++;
		n--;
	}
	if (n == 0)
		return (0);
	return ((unsigned char)*a - (unsigned char)*b);
}

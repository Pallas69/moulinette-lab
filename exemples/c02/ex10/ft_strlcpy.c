unsigned int	ft_strlcpy(char *dest, char *src, unsigned int size)
{
	unsigned int	i;
	unsigned int	len;

	len = 0;
	while (src[len])
		len++;
	i = 0;
	if (size > 0)
	{
		while (i + 1 < size && src[i])
		{
			dest[i] = src[i];
			i++;
		}
		dest[i] = 0;
	}
	return (len);
}

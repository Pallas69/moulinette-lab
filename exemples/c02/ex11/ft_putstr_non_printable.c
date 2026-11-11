#include <unistd.h>

void	ft_putstr_non_printable(char *str)
{
	unsigned int	i;
	unsigned char	c;
	char			*hex;

	hex = "0123456789abcdef";
	i = 0;
	while (str[i])
	{
		c = (unsigned char)str[i];
		if (c >= 32 && c <= 126)
			write(1, &str[i], 1);
		else
		{
			write(1, "\\", 1);
			write(1, &hex[c / 16], 1);
			write(1, &hex[c % 16], 1);
		}
		i++;
	}
}

#include <unistd.h>
#include "ft_hexdump.h"

static void	hexbyte(unsigned char byte)
{
	char	*digits;

	digits = "0123456789abcdef";
	write(1, &digits[byte / 16], 1);
	write(1, &digits[byte % 16], 1);
}

void	ft_offset(unsigned int position)
{
	char	out[8];
	char	*digits;
	int		i;

	digits = "0123456789abcdef";
	i = 7;
	while (i >= 0)
	{
		out[i] = digits[position % 16];
		position /= 16;
		i--;
	}
	write(1, out, 8);
}

static void	hex_columns(unsigned char *data, int count)
{
	int	i;

	i = 0;
	while (i < 16)
	{
		if (i < count)
			hexbyte(data[i]);
		else
			write(1, "  ", 2);
		if (i == 7)
			write(1, "  ", 2);
		else
			write(1, " ", 1);
		i++;
	}
}

static void	ascii_column(unsigned char *data, int count)
{
	int	i;

	i = 0;
	while (i < count)
	{
		if (data[i] >= 32 && data[i] <= 126)
			write(1, &data[i], 1);
		else
			write(1, ".", 1);
		i++;
	}
}

void	ft_line(unsigned char *data, int count, unsigned int position)
{
	ft_offset(position);
	write(1, "  ", 2);
	hex_columns(data, count);
	write(1, " |", 2);
	ascii_column(data, count);
	write(1, "|\n", 2);
}

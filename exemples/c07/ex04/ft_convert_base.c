#include <stdlib.h>

int		base_size(char *base);
long	read_base(char *s, char *base, int len);

static int	digit_count(long value, int len)
{
	int	n;

	n = 1;
	while (value >= len)
	{
		value /= len;
		n++;
	}
	return (n);
}

static char	*format_number(long value, char *base, int len)
{
	long	magnitude;
	int		size;
	char	*out;

	magnitude = value;
	if (value < 0)
		magnitude = -value;
	size = digit_count(magnitude, len) + (value < 0);
	out = malloc(size + 1);
	if (!out)
		return (0);
	out[size] = 0;
	while (size > (value < 0))
	{
		out[--size] = base[magnitude % len];
		magnitude /= len;
	}
	if (value < 0)
		out[0] = '-';
	return (out);
}

char	*ft_convert_base(char *nbr, char *base_from, char *base_to)
{
	int	from_len;
	int	to_len;

	from_len = base_size(base_from);
	to_len = base_size(base_to);
	if (!from_len || !to_len)
		return (0);
	return (format_number(read_base(nbr, base_from, from_len),
			base_to, to_len));
}

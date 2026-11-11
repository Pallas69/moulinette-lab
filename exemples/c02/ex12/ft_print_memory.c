#include <unistd.h>
#include <stdint.h>

static void	put_address(uintptr_t value)
{
	char	*hex;
	char	out[16];
	int		i;

	hex = "0123456789abcdef";
	i = 15;
	while (i >= 0)
	{
		out[i] = hex[value % 16];
		value = value / 16;
		i--;
	}
	write(1, out, 16);
	write(1, ": ", 2);
}

static void	put_hex(unsigned char *p, unsigned int count)
{
	unsigned int	i;
	char			*hex;

	hex = "0123456789abcdef";
	i = 0;
	while (i < 16)
	{
		if (i < count)
		{
			write(1, &hex[p[i] / 16], 1);
			write(1, &hex[p[i] % 16], 1);
		}
		else
			write(1, "  ", 2);
		if (i % 2 == 1)
			write(1, " ", 1);
		i++;
	}
}

static void	put_chars(unsigned char *p, unsigned int count)
{
	unsigned int	i;

	i = 0;
	while (i < count)
	{
		if (p[i] >= 32 && p[i] <= 126)
			write(1, &p[i], 1);
		else
			write(1, ".", 1);
		i++;
	}
	write(1, "\n", 1);
}

void	*ft_print_memory(void *addr, unsigned int size)
{
	unsigned char	*p;
	unsigned int	off;
	unsigned int	count;

	p = addr;
	off = 0;
	while (off < size)
	{
		count = size - off;
		if (count > 16)
			count = 16;
		put_address((uintptr_t)(p + off));
		put_hex(p + off, count);
		put_chars(p + off, count);
		off += count;
	}
	return (addr);
}

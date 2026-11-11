#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <libgen.h>
#include "ft_cat.h"

static void	put_error(char *s)
{
	while (*s)
		write(2, s++, 1);
}

void	ft_error(char *program, char *file)
{
	put_error(basename(program));
	put_error(": ");
	put_error(file);
	put_error(": ");
	put_error(strerror(errno));
	put_error("\n");
}

int	ft_copy(int fd)
{
	char		buf[4096];
	ssize_t		n;

	n = read(fd, buf, sizeof(buf));
	while (n > 0)
	{
		if (write(1, buf, n) != n)
			return (1);
		n = read(fd, buf, sizeof(buf));
	}
	return (n < 0);
}

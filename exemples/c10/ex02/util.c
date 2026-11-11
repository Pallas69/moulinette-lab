#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <libgen.h>
#include "ft_tail.h"

int	ft_number(char *s)
{
	int	n;

	n = 0;
	while (*s >= '0' && *s <= '9')
	{
		n = n * 10 + (*s - '0');
		s++;
	}
	return (n);
}

void	ft_text(char *s)
{
	while (*s)
		write(1, s++, 1);
}

static void	error_text(char *s)
{
	while (*s)
		write(2, s++, 1);
}

void	ft_error(char *program, char *file)
{
	error_text(basename(program));
	error_text(": ");
	error_text(file);
	error_text(": ");
	error_text(strerror(errno));
	error_text("\n");
}

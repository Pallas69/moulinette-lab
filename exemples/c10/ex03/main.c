#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <libgen.h>
#include "ft_hexdump.h"

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

static int	input_files(int argc, char **argv, t_dump *state)
{
	int	i;
	int	fd;
	int	error;

	i = 2;
	error = 0;
	while (i < argc)
	{
		fd = open(argv[i], O_RDONLY);
		if (fd < 0)
		{
			ft_error(argv[0], argv[i]);
			error = 1;
		}
		else
		{
			if (ft_input(fd, state))
				error = 1;
			close(fd);
		}
		i++;
	}
	return (error);
}

int	main(int argc, char **argv)
{
	t_dump	state;
	int		error;

	ft_init(&state);
	if (argc <= 2)
		error = ft_input(0, &state);
	else
		error = input_files(argc, argv, &state);
	ft_finish(&state);
	return (error);
}

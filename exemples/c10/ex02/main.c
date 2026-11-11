#include <unistd.h>
#include <fcntl.h>
#include "ft_tail.h"

static void	header(char *name, int newline)
{
	if (newline)
		ft_text("\n");
	ft_text("==> ");
	ft_text(name);
	ft_text(" <==\n");
}

int	ft_files(int argc, char **argv, int count, int start)
{
	int	i;
	int	fd;
	int	error;

	i = start;
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
			if (argc - start > 1)
				header(argv[i], i > start);
			if (ft_stream(fd, count))
				error = 1;
			close(fd);
		}
		i++;
	}
	return (error);
}

int	main(int argc, char **argv)
{
	int	count;
	int	start;

	if (argc < 2 || argv[1][0] != '-' || argv[1][1] != 'c')
		return (1);
	start = 2;
	if (argv[1][2])
		count = ft_number(argv[1] + 2);
	else
	{
		if (argc < 3)
			return (1);
		count = ft_number(argv[2]);
		start = 3;
	}
	if (argc == start)
		return (ft_stream(0, count));
	return (ft_files(argc, argv, count, start));
}

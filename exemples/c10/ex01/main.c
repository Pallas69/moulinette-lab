#include <unistd.h>
#include <fcntl.h>
#include "ft_cat.h"

static int	copy_arg(char *name, char *program)
{
	int	fd;
	int	result;

	if (name[0] == '-' && !name[1])
		return (ft_copy(0));
	fd = open(name, O_RDONLY);
	if (fd < 0)
	{
		ft_error(program, name);
		return (1);
	}
	result = ft_copy(fd);
	if (result)
		ft_error(program, name);
	close(fd);
	return (result);
}

int	main(int argc, char **argv)
{
	int	i;
	int	error;

	if (argc == 1)
		return (ft_copy(0));
	i = 1;
	error = 0;
	while (i < argc)
	{
		if (copy_arg(argv[i], argv[0]))
			error = 1;
		i++;
	}
	return (error);
}

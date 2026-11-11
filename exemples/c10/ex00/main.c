#include <unistd.h>
#include <fcntl.h>

static int	copy_file(char *name)
{
	int			fd;
	char		buf[4096];
	ssize_t		n;

	fd = open(name, O_RDONLY);
	if (fd < 0)
		return (1);
	n = read(fd, buf, sizeof(buf));
	while (n > 0)
	{
		write(1, buf, n);
		n = read(fd, buf, sizeof(buf));
	}
	close(fd);
	return (n < 0);
}

int	main(int argc, char **argv)
{
	if (argc < 2)
		write(2, "File name missing.\n", 19);
	else if (argc > 2)
		write(2, "Too many arguments.\n", 20);
	else if (copy_file(argv[1]))
		write(2, "Cannot read file.\n", 18);
	else
		return (0);
	return (1);
}

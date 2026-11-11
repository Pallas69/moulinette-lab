#include <unistd.h>
#include <stdlib.h>
#include "ft_tail.h"

static int	read_all(int fd, t_buffer *data)
{
	char		chunk[1024];
	ssize_t		n;
	int			i;

	n = read(fd, chunk, sizeof(chunk));
	while (n > 0)
	{
		if (ft_reserve(data, n))
			return (1);
		i = 0;
		while (i < n)
		{
			data->data[data->length++] = chunk[i];
			i++;
		}
		n = read(fd, chunk, sizeof(chunk));
	}
	return (n < 0);
}

int	ft_stream(int fd, int count)
{
	t_buffer	data;
	int			error;

	data.data = 0;
	data.length = 0;
	data.capacity = 0;
	error = read_all(fd, &data);
	if (count > data.length)
		count = data.length;
	if (count > 0)
		write(1, data.data + data.length - count, count);
	free(data.data);
	return (error);
}

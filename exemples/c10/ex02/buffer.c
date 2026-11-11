#include <stdlib.h>
#include "ft_tail.h"

int	ft_reserve(t_buffer *buffer, int extra)
{
	int		capacity;
	int		i;
	char	*copy;

	if (buffer->length + extra <= buffer->capacity)
		return (0);
	capacity = buffer->capacity;
	if (!capacity)
		capacity = 2048;
	while (capacity < buffer->length + extra)
		capacity *= 2;
	copy = malloc(capacity);
	if (!copy)
		return (1);
	i = 0;
	while (i < buffer->length)
	{
		copy[i] = buffer->data[i];
		i++;
	}
	free(buffer->data);
	buffer->data = copy;
	buffer->capacity = capacity;
	return (0);
}

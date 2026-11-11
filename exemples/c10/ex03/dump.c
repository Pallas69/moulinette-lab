#include <unistd.h>
#include "ft_hexdump.h"

void	ft_init(t_dump *state)
{
	state->position = 0;
	state->used = 0;
	state->has_previous = 0;
	state->repeated = 0;
}

static int	equal_lines(t_dump *state)
{
	int	i;

	i = 0;
	while (i < 16)
	{
		if (state->current[i] != state->previous[i])
			return (0);
		i++;
	}
	return (1);
}

static void	emit_full(t_dump *state)
{
	int	i;

	if (state->has_previous && equal_lines(state))
	{
		if (!state->repeated)
			write(1, "*\n", 2);
		state->repeated = 1;
	}
	else
	{
		ft_line(state->current, 16, state->position);
		state->repeated = 0;
	}
	i = 0;
	while (i < 16)
	{
		state->previous[i] = state->current[i];
		i++;
	}
	state->has_previous = 1;
	state->position += 16;
	state->used = 0;
}

int	ft_input(int fd, t_dump *state)
{
	unsigned char	byte;
	ssize_t			n;

	n = read(fd, &byte, 1);
	while (n > 0)
	{
		state->current[state->used++] = byte;
		if (state->used == 16)
			emit_full(state);
		n = read(fd, &byte, 1);
	}
	return (n < 0);
}

void	ft_finish(t_dump *state)
{
	if (state->used)
	{
		ft_line(state->current, state->used, state->position);
		state->position += state->used;
	}
	if (state->position)
	{
		ft_offset(state->position);
		write(1, "\n", 1);
	}
}

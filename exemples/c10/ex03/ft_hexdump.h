#ifndef FT_HEXDUMP_H
# define FT_HEXDUMP_H

typedef struct s_dump
{
	unsigned char	current[16];
	unsigned char	previous[16];
	unsigned int	position;
	int				used;
	int				has_previous;
	int				repeated;
}	t_dump;

void	ft_offset(unsigned int position);
void	ft_line(unsigned char *data, int count, unsigned int position);
void	ft_init(t_dump *state);
int		ft_input(int fd, t_dump *state);
void	ft_finish(t_dump *state);
void	ft_error(char *program, char *file);

#endif

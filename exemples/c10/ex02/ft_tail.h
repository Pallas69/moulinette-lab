#ifndef FT_TAIL_H
# define FT_TAIL_H

typedef struct s_buffer
{
	char	*data;
	int		length;
	int		capacity;
}	t_buffer;

int		ft_number(char *s);
void	ft_text(char *s);
void	ft_error(char *program, char *file);
int		ft_reserve(t_buffer *buffer, int extra);
int		ft_stream(int fd, int count);
int		ft_files(int argc, char **argv, int count, int start);

#endif

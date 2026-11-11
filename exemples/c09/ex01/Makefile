NAME = libft.a
CC = cc
CFLAGS = -Wall -Wextra -Werror -Iincludes
SRC = srcs/ft_putchar.c srcs/ft_swap.c srcs/ft_putstr.c srcs/ft_strlen.c srcs/ft_strcmp.c
OBJ = $(SRC:.c=.o)

all: $(NAME)

$(NAME): $(OBJ)
	ar rc $(NAME) $(OBJ)

srcs/%.o: srcs/%.c includes/ft.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re

NAME = ft_display_file
CC = cc
CFLAGS = -Wall -Wextra -Werror

all: $(NAME)

$(NAME): main.o
	$(CC) $(CFLAGS) main.o -o $(NAME)

main.o: main.c
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	rm -f main.o

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re

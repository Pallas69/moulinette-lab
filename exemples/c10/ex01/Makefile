NAME = ft_cat
CC = cc
CFLAGS = -Wall -Wextra -Werror

all: $(NAME)

$(NAME): main.o io.o
	$(CC) $(CFLAGS) main.o io.o -o $(NAME)

io.o: io.c ft_cat.h
	$(CC) $(CFLAGS) -c io.c -o io.o

main.o: main.c ft_cat.h
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	rm -f main.o io.o

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re

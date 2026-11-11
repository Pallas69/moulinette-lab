#include "do_op.h"

static int	operation_index(char *s)
{
	char	*ops;
	int		i;

	ops = "+-*/%";
	i = 0;
	while (i < 5)
	{
		if (s[0] == ops[i] && s[1] == 0)
			return (i);
		i++;
	}
	return (-1);
}

static int	zero_error(int op, int b)
{
	if (b != 0 || (op != 3 && op != 4))
		return (0);
	if (op == 3)
		ft_text("Stop : division by zero\n");
	else
		ft_text("Stop : modulo by zero\n");
	return (1);
}

static void	dispatch(int op, int a, int b)
{
	int	(*fn[5])(int, int);

	fn[0] = op_add;
	fn[1] = op_sub;
	fn[2] = op_mul;
	fn[3] = op_div;
	fn[4] = op_mod;
	if (op < 0)
		ft_text("0\n");
	else if (!zero_error(op, b))
	{
		ft_number_out(fn[op](a, b));
		ft_text("\n");
	}
}

int	main(int argc, char **argv)
{
	if (argc == 4)
		dispatch(operation_index(argv[2]), ft_number(argv[1]),
			ft_number(argv[3]));
	return (0);
}

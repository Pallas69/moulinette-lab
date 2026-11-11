#ifndef FT_BTREE_H
# define FT_BTREE_H

typedef struct s_btree
{
	struct s_btree	*left;
	struct s_btree	*right;
	void			*item;
}	t_btree;

typedef struct s_state
{
	int		first;
	void	(*f)(void *, int, int);
}			t_state;

t_btree	*btree_create_node(void *item);

#endif

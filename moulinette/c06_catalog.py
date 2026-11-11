"""Programmes C 06 v8 : tests d'arguments, sans harnais de fonction."""
C06_EXERCISES={}
argsets=[('aucun argument',[]),('un argument',['bonjour']),('trois arguments',['zeta','Alpha','beta']),
         ('vides et doublons',['','a','a','','B']),('majuscules et minuscules',['z','A','a','Z','0',' ']),
         ('espaces et ponctuation',['a b','a-b','a_b','a.b']),('nombres textuels',['10','2','01','1'])]
for i,name in enumerate(('ft_print_program_name','ft_print_params','ft_rev_params','ft_sort_params')):
 cases=[]
 for label,args in argsets:
  vals=args if i==1 else list(reversed(args)) if i==2 else sorted(args) if i==3 else []
  expected=b'__PROGRAM_NAME__' if i==0 else ''.join(v+'\n' for v in vals).encode()
  cases.append((label,args,expected))
 C06_EXERCISES[f'c06/ex{i:02}']={'source':name+'.c','executable':'test-'+name,'subject_version':'8',
      'allowed_functions':{'write'},'prototype':'/* programme : liaison directe */\n','harness':'/* sans harnais */\n',
      'kind':'program','cases':cases}

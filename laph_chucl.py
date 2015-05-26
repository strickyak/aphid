def Eval(vec, lookup_fn, command_factory):
  say vec
  must type(vec) is list
  cmd = vec[0]
  must cmd.isBare(), type(cmd), cmd
  cmd = cmd.a
  vec = vec[1:]

  # First look for special forms.
  switch cmd:
    case 'if':
      raise 'TODO'
    case 'fn':
      return command_factory(vec)

  args = []
  for a in vec:
    say 'ARG:', a

    if a.isBare():
        say 'Bare', a.a
        args.append(a.a)
    elif a.isDollar():
        say 'Dollar', a.a
        args.append(lookup_fn(a.a))
    else:
        raise 'TODO', type(a), a, vec
    say 'ARGS:', args

  # Special code for the many binary operators.
  if len(args) == 2:
    x, y = args
    switch cmd:
      case '++':
        return x + y
      case '+':
        return str(float(x) + float(y))
      case '-':
        return str(float(x) - float(y))
      case '*':
        return str(float(x) * float(y))
      case '/':
        return str(float(x) / float(y))
      case '//':
        return str(float(x) // float(y))
      case '%':
        return str(float(x) % float(y))
      case '<':
        return str(float(x) < float(y))
      case '<=':
        return str(float(x) <= float(y))
      case '==':
        return str(float(x) == float(y))
      case '!=':
        return str(float(x) != float(y))
      case '>':
        return str(float(x) > float(y))
      case '>=':
        return str(float(x) >= float(y))
      case 'split':
        return y.split(x)  # (split ch str)
      case 'join':
        return x.join(y)   # (join sep strs)

      # String comparison
      case 'lt':
        return str(x < y)
      case 'le':
        return str(x <= y)
      case 'eq':
        return str(x == y)
      case 'ne':
        return str(x != y)
      case 'gt':
        return str(x > y)
      case 'ge':
        return str(x >= y)

  # Fall through for other cases.
  switch cmd:
    case '++':
      return ''.join([x for x in args])

    case '+':
      return str(sum([float(x) for x in args]))
    case '*':
      return reduce((lambda a,b: a*b), [float(x) for x in args])

  raise 'No such Chucl command: %q (or wrong number of args: %d)' % (cmd, len(args))


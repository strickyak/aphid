from go import path as P

###############################
# Path Manipulation
B = P.Base
C = P.Clean
D = P.Dir
def J(*args):
  return C(P.Join(*args))
def S(s):
  if s.startswith('/'):
    return ['/'] + [e for e in s.split('/') if e]
  else:
    return [e for e in s.split('/') if e]
def R(path, rel):
  if path.startswith('/'):
    return C(path)
  else:
    return J(rel, path)

class Binding:
  def __init__(key, value, next):
    .key = key
    .value = value
    .next = next

class Evaluator:
  def __init__(lookup_fn):
    .lookup_fn = lookup_fn

  def Lookup(k, dirpath, binding):
    say k
    # First try looking in the binding.
    while binding:
      if binding.key == k:
        return binding.value
      binding = binding.next
    # Then use the provided lookup_fn.
    say k, dirpath, (R(k, dirpath))
    return .lookup_fn(R(k, dirpath))

  def EvalPath(path, rel='/', binding=None):
    say path
    path = R(path, rel)
    p = .lookup_fn(path)
    return .EvalNode(p, D(path), binding)

  def EvalNode(p, dirpath, binding):
    say p, dirpath, binding

    switch type(p):
      case dict:
        return p
      case str:
        return p
      case list:
        return p

    if p.isBare():
      return p.a

    if p.isDollar():
      k = R(p.a, dirpath)
      q = .Lookup(k, '/', binding)
      dirpath2 = D(k)
      return .EvalNode(q, dirpath2, binding)

    if p.isCommand():
      return .EvalCommand(p, dirpath, binding)

    raise 'EvalNode cannot eval node of type %v' % type(p)

  def EvalCommand(p, dirpath, binding):
    vec = p.vec
    say vec, dirpath, binding
    must type(vec) is list, vec
    must len(vec), vec
    cmd = vec[0]

    # Dereference if cmd is a Dollar.
    if cmd.isDollar():
      cmd = .EvalNode(cmd, dirpath, binding)

    # If cmd is lambda expression:
    if type(cmd) is list:
      must len(cmd) == 3, vec
      fn, formals, body = cmd
      must fn == "fn", vec
      must formals.isCommand(), vec # Actually, a vec of formal parameters.
      must len(formals) == len(vec) - 1  # Correct number of args to formals.

      binding2 = binding
      for f, v in zip(formals, vec[1:]):
        binding2 = Binding(f, v, binding2)
      return .EvalNode(body, dirpath, binding2)

    must cmd.isBare(), type(cmd), cmd
    cmd = cmd.a
    vec = vec[1:]

    # Handle special forms.
    switch cmd:
      case 'if':
        raise 'TODO'
      case 'fn':
        return p

    # Handle other builtins.
    args = []
    for a in vec:
      say 'Raw ARG:', a

    args = [.EvalNode(a, dirpath, binding) for a in vec]
    for a in args:
      say 'Evaluated ARG:', a

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

pass

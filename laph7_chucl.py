from go import path as P

###############################
# Path Manipulation
B = P.Base
C = P.Clean
D = P.Dir
def J(*args):
  """Join"""
  return C(P.Join(*args))

def R(path, rel):
  if path.startswith('/'):
    return C(path)
  else:
    return J(rel, path)

def H(path):
  """Head of path (the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return vec[0] if vec else ''

#def S(s):
#  """Split Somehow?"""
#  if s.startswith('/'):
#    return ['/'] + [e for e in s.split('/') if e]
#  else:
#    return [e for e in s.split('/') if e]
def Absolute(path, rel):
  """Resolve Relative or Absolute to Absoulte"""
  if path.startswith('/'):
    return C(path)
  else:
    return J(rel, path)

class Binding:
  def __init__(key, value, next):
    .key = key
    .value = value
    .next = next
def Simple(a):
  switch type(a):
    case str:
      return a
    case int:
      return a
    case list:
      return a
  if a.isCommand():
    return a.vec
  if a.isBare():
    return a.a
  if a.isDollar():
    raise 'dollar?', a
  raise 'what?', a

class Evaluator:
  def __init__(lookup_fn, command_ctor, value_ctor):
    .lookup_fn = lookup_fn
    .command_ctor = command_ctor
    .value_ctor = value_ctor

  def Lookup(k, dirpath, binding):
    # First try looking in the binding.
    say k, dirpath, binding
    while binding:
      say k, binding.key
      if binding.key == k:
        return binding.value
      binding = binding.next
    # Then use the provided lookup_fn.
    return .lookup_fn(Absolute(k, dirpath))

  def EvalPath(path, rel='/', binding=None):
    say '<EP<', path, rel
    apath = Absolute(path, rel)
    node = .lookup_fn(apath)
    z = .EvalNode(node, apath, binding)
    say '>EP>', apath, z, node
    #print "YAK_EvalPath: %-20s ==> %20s ==> %s" % (apath, z, node)
    return z
  
  def EvalNode(node, path, binding):
    Cpath = C(path)
    Dpath = D(Cpath)
    say '<EN<', node, path, Cpath

    if not node:
      say '>>', node, '>>None'
      return None

    if node.IsDir():
      must type(node.names) is list, node.names
      say '>>', node, '>>IsDir>>', node
      return node

    must node.IsLeaf(), node
    leaf = node.leaf
    if leaf.isBare():
      say '>>', node, '>>leaf.isBare>>', node
      return node

    if leaf.isDollar():
      say leaf.a
      if leaf.a.startswith('/') or leaf.a.startswith('./') or leaf.a.startswith('../'):
        # Absolute path was given.
        Qpath = R(leaf.a, Dpath)
      else:
        # Search for the head name.
        h = H(leaf.a)
        d = Dpath
        while True:
          say leaf.a, h, d, Cpath
          maybe = .Lookup(R(h, d), '/', binding)
          if maybe: break
          if d == '' or d == '/': break
          d = D(d)
        if not maybe:
          say h, leaf.a
          raise 'Dollar: Cannot find %q from path %q starting at %q' % (h, leaf.a, Cpath)
        Qpath = J(d, leaf.a)

      q = .Lookup(Qpath, '/', binding)
      say '->', node, Qpath, '>>leaf.isDollar....', q
      z = .EvalNode(q, Qpath, binding)
      say '>>', node, Qpath, '>>leaf.isDollar>>', z
      return z

    if leaf.isCommand():
      say '->', node, Cpath, '>>leaf.isCommand....'
      z = .EvalCommand(leaf, Cpath, binding)
      say '>>', node, Cpath, '>>leaf.isCommand>>', z
      return z

    raise 'EvalNode cannot eval node of type %v' % type(node)

  def EvalCommand(leaf, Cpath, binding):
    say '<EvalCommand<', leaf, Cpath, binding
    try:
      z = .EvalCommand2(leaf, Cpath, binding)
      say '>EvalCommand>', leaf, Cpath, binding, '>EC>', z
      return .value_ctor(z)
    except as ex:
      # TODO: Stop evalling commands too early.
      say('EXCEPTION(%s)' % ex)
      return .value_ctor('EXCEPTION(%s)' % ex)

  def EvalCommand2(leaf, Cpath, binding):
    cmdvec = leaf.cmdvec
    say cmdvec, Cpath, binding
    must type(cmdvec) is list, cmdvec
    must len(cmdvec), cmdvec
    cmd = cmdvec[0].leaf

    # Dereference if cmd is a Dollar.
    if cmd.isDollar():
      cmd = .EvalNode(cmd, Cpath, binding)

    # If cmd is lambda expression:
    if cmd.isCommand():
      raise 'Lambdas not tested yet'
      vec2 = cmd.cmdvec
      must len(vec2) == 3, vec2
      fn, formals, body = vec2
      must fn.isBare(), vec2
      must fn.a == "fn", vec2
      must formals.isCommand(), vec2  # Actually, a vec of formal parameters.
      must len(formals.cmdvec) == len(cmdvec) - 1  # Correct number of args to formals.

      binding2 = binding
      for f, v in zip(formals.cmdvec, cmdvec[1:]):
        binding2 = Binding(f.a, v, binding2)
      return .EvalNode(body, Cpath, binding2)

    must cmd.isBare(), type(cmd), cmd
    cmd = cmd.a
    cmdvec = cmdvec[1:]

    # Handle special forms.
    switch cmd:
      case 'fn':
        return leaf  # Lambda exprs eval to themselves.
      case 'if':
        must len(cmdvec) == 3, cmdvec
        x, y, z = cmdvec
        #say x, y, v
        xv = Simple(.EvalNode(x, Cpath, binding))
        #say xv
        if xv and xv!='False':
          # True branch.
          #say 'True', y
          return .EvalNode(y, Cpath, binding)
        else:
          # False branch.
          #say 'False', z
          return .EvalNode(z, Cpath, binding)

    # Handle other builtins.
    args = []
    #for a in vecmdvec:
    #  #say 'Raw ARG:', a

    say cmdvec
    args = []
    for a in cmdvec:
      x = .EvalNode(a, Cpath, binding)
      if x and x.IsDir():
        say 'YAK GOT DirNode FROM EvalNode', a, Cpath, binding
      args.append(x.leaf.a if x else None) 
    say args

    switch cmd:
      case 'error':
        raise 'ERROR(%s)' % str(args)

    # Special code for the many binary operators.
    if len(args) == 1:
      x, = args
      switch cmd:
        case 'range':
          return [str(e) for e in range(int(x))]
        case 'length':
          z = str(len(Simple(x)))
          return z
        case 'error':
          z = 'ERROR(%s)' % x

    if len(args) == 2:
      x, y = args
      say x, y
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

        case 'map':
          return [.EvalCommand(.command_ctor([x, e]), Cpath, binding) for e in y]

    # Fall through for other cases.
    switch cmd:
      case '++':
        return ''.join([x for x in args])

      case '+':
        return str(sum([float(x) for x in args]))
      case '*':
        return reduce((lambda a,b: a*b), [float(x) for x in args])
      case 'list':
        return args

    raise 'No such Chucl command: %q (or wrong number of args: %d)' % (cmd, len(args))

pass

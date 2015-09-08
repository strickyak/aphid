from go import path as P

class Lambda:
  def __init__(formals, body):
    .formals = formals
    .body = body

class Directory:
  def __init__(names):
    .names = names
  def __repr__():
    return 'D{%s}' % ','.join(.names)

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

def Absolute(path, rel):
  """Resolve Relative or Absolute to Absoulte"""
  if path.startswith('/'):
    return C(path)
  else:
    return J(rel, path)


class Chucl:
  def __init__(lookup_fn):
    .lookup_fn = lookup_fn

  def EvalPathThing(path, rel='/', binding=None):
    # Look in binding for the path (if it has no '/').
    if binding and not ('/' in path):
      if path in binding:
        return binding[path]

    # THIS IS THE UPLOOKING CODE.
    if path.startswith('/') or path.startswith('./') or path.startswith('../'):
      # Specific path was given; do not do up-looking.
      Qpath = R(path, rel)
    else:
      # Search for the head name.
      h = H(path)
      d = rel
      while True:
        maybe = .lookup_fn(R(h, d))
        if maybe: break
        if d == '.' or d == '' or d == '/': break
        d = D(d)
      if not maybe:
        say h, path
        raise 'Dollar: Cannot find %q from path %q starting at %q' % (h, path, rel)
      Qpath = R(path, d)  # Rejoin d with entire path.

    # Now that you know how far up to go, lookup the final result.
    thing = .lookup_fn(Qpath)
    # And eval the result with Chucl.
    z = .EvalChucl(thing, Qpath, binding)
    return z

  def EvalChucl(thing, path, binding):
    if thing is None:
      return None

    Cpath = C(path)
    Dpath = D(Cpath)

    switch repr(type(thing)):
      case 'Directory':
        return thing

    switch type(thing):
      case str:
        say '>>', thing, '>>leaf.isBare>>', thing

        if thing.startswith('$'):
          q = thing[1:]
          say '<<leaf.isDollar<<', q
          z = .EvalPathThing(q, Dpath, binding)
          say '>>', path, thing, q, Dpath, '>>leaf.isDollar>>', z
          must not z or type(z) is str
          return z
        else:
          return thing

      case list:
        say '->', thing, Cpath, '>>leaf.isCommand....'
        z = .EvalCommand(thing, Cpath, binding)
        say '>>', thing, Cpath, '>>leaf.isCommand>>', z
        return z

    raise 'EvalChucl cannot eval node of type %v' % type(thing)
  
  def EvalCommand(in_vec, Cpath, binding):
    vec = [(None if e is None else .EvalChucl(e, Cpath, binding)) for e in in_vec]

    cmd, args = vec[0], vec[1:]
    switch cmd:
      case '++':
        return ''.join(args)
      case '+':
        return str(sum([int(x) for x in args]))
      case '*':
        return str(reduce(lambda a, b: int(a)*int(b), args, 1))
    raise 'EvalCommand: unknown cmd: %q' % cmd

#  def EvalCommand2(leaf, Cpath, binding):
#    raise 666
#    cmdvec = leaf.cmdvec
#    say cmdvec, Cpath, binding
#    must type(cmdvec) is list, cmdvec
#    must len(cmdvec), cmdvec
#    cmd = cmdvec[0].leaf
#
#    # Dereference if cmd is a Dollar.
#    if cmd.isBare() and cmd.a.startswith('$'):
#      cmd = .EvalPath(cmd.a[1:], D(Cpath), binding).leaf
#      say cmd
#
#    say cmd.isCommand(), type(cmd), cmd
#    # If cmd is lambda expression:
#    if cmd.isCommand():
#      #raise 'Lambdas not tested yet'
#      vec2 = cmd.cmdvec
#      must len(vec2) == 3, vec2
#      fn, formals, body = vec2
#      say type(fn), fn, type(formals), formals
#      must fn.leaf.isBare(), vec2
#      must fn.leaf.a == "fn", vec2
#      must formals.leaf.isCommand(), vec2  # Actually, a vec of formal parameters.
#      must len(formals.leaf.cmdvec) == len(cmdvec) - 1  # Correct number of args to formals.
#
#      binding2 = binding
#      for f, v in zip(formals.leaf.cmdvec, cmdvec[1:]):
#        raise 'binding2 = Binding(f.leaf.a, v, binding2)'
#        say f, v, binding2
#      z = .EvalNode(body, Cpath, binding2)
#      say vec2, z
#      return z
#
#    must cmd.isBare(), type(cmd), cmd
#    cmd = cmd.a
#    cmdvec = cmdvec[1:]
#
#    # Handle special forms.
#    switch cmd:
#      case 'lambda':
#        return leaf  # Lambda exprs eval to themselves.
#      case 'if':
#        must len(cmdvec) == 3, cmdvec
#        x, y, z = cmdvec
#        xv = .EvalNode(x, Cpath, binding)
#        s = xv.leaf.a if xv else None
#        if xv and xv!='False':
#          # True branch.
#          return .EvalNode(y, Cpath, binding)
#        else:
#          # False branch.
#          return .EvalNode(z, Cpath, binding)
#
#    # Handle other builtins.
#    args = []
#
#    say cmdvec
#    args = []
#    for a in cmdvec:
#      x = .EvalNode(a, Cpath, binding)
#      if x and x.IsDir():
#        say 'YAK GOT DirNode FROM EvalNode', a, Cpath, binding
#      args.append((x.leaf.a if x.leaf.isBare() else x.leaf.cmdvec) if x else None) 
#    say args
#
#    switch cmd:
#      case 'error':
#        raise 'ERROR(%s)' % str(args)
#
#    # Special code for the many binary operators.
#    if len(args) == 1:
#      x, = args
#      switch cmd:
#        case 'range':
#          return [str(e) for e in range(int(x))]
#        #case 'length':
#        #  z = str(len(Simple(x)))
#        #  return z
#        case 'error':
#          z = 'ERROR(%s)' % x
#
#    if len(args) == 2:
#      x, y = args
#      say x, y
#      switch cmd:
#        case '++':
#          return x + y
#        case '+':
#          return str(float(x) + float(y))
#        case '-':
#          return str(float(x) - float(y))
#        case '*':
#          return str(float(x) * float(y))
#        case '/':
#          return str(float(x) / float(y))
#        case '//':
#          return str(float(x) // float(y))
#        case '%':
#          return str(float(x) % float(y))
#        case '<':
#          return str(float(x) < float(y))
#        case '<=':
#          return str(float(x) <= float(y))
#        case '==':
#          return str(float(x) == float(y))
#        case '!=':
#          return str(float(x) != float(y))
#        case '>':
#          return str(float(x) > float(y))
#        case '>=':
#          return str(float(x) >= float(y))
#        case 'split':
#          return y.split(x)  # (split ch str)
#        case 'join':
#          return x.join(y)   # (join sep strs)
#
#        # String comparison
#        case 'lt':
#          return str(x < y)
#        case 'le':
#          return str(x <= y)
#        case 'eq':
#          return str(x == y)
#        case 'ne':
#          return str(x != y)
#        case 'gt':
#          return str(x > y)
#        case 'ge':
#          return str(x >= y)
#
#        case 'map':
#          return [.EvalCommand(.command_ctor([x, e]), Cpath, binding) for e in y]
#
#    # Fall through for other cases.
#    switch cmd:
#      case '++':
#        return ''.join([x for x in args])
#
#      case '+':
#        return str(sum([float(x) for x in args]))
#      case '*':
#        return reduce((lambda a,b: a*b), [float(x) for x in args])
#      case 'list':
#        return args
#
#    raise 'No such Chucl command: %q (or wrong number of args: %d)' % (cmd, len(args))

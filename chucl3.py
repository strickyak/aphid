# Chucl lisp-like interpreter for laph3
#
# t = Chucl(tree)
#
# tree must be a toplevel dict.
# Nested dicts as values form the tree.
# Leaves may be
#   str: A final str value.
#   list: A final list value.
#   tuple: A chucl expression to be evaluated.

from go import path as P
from rye_lib import data

###############################
# Path Manipulation
C = P.Clean
D = P.Dir
def J(*args):
  return C(P.Join(*args))
def RelativeTo(path, rel):
  if path.startswith('/'):
    return C(path)
  else:
    return J(rel, path)
def H(path):
  """Head of path (the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return vec[0] if vec else ''
def T(path):
  """Tail of path (all but the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return J(*vec[1:]) if len(vec) > 1 else ''
def HT(path):
  return H(path), T(path)
def S(path):
  return [e for e in path.split('/') if e]
###############################


class Chucl:
  def __init__(tree):
    .tree = tree

  def Find(path):
    def recurse(d, p):
      if not p: return d
      h, t = HT(p)
      dh = d.get(h, None)
      if dh is None:
        raise 'Find: cannot find key %q in path %q' % (h, path)
      if t and type(dh) is dict:
        return recurse(dh, t)
      if t:
        raise 'Find: cannot use tail key %q in object %v in path %q' % (t, dh, path)
      return dh
    return recurse(.tree, path)

  def Eval(path, depth=0, env=None):
    if env:
      # First look in the env for the path.
      for k, v in env:
        if k == path:
          return v

    if depth > 100:
      raise 'Eval: too deep in path %q' % path
    try:
      x = .Find(path)
    except as ex:
      raise 'Eval: exception in path %q: %v' % (path, ex)

    if x is None:
      raise 'Eval: got None for Eval path %q' % path

    switch type(x):
      case str:
        return x
      case list:
        return x
      case tuple:
        return .EvalTuple(x, path, depth+1, env)
    raise 'Eval path %q: bad type %q in %v' % (path, type(x), x)

  def EvalTuple(x, path, depth, env):
    say (x, path, depth, env)
    dpath = D(path)

    def evalIt(e):
      switch type(e):
        case str:
          z = .Eval(RelativeTo(e[1:], dpath), depth, env) if (type(e) is str and e.startswith('$')) else e
        case list:
          z = e
        case tuple:
          z = .EvalTuple(e, path, depth+1, env)
        default:
          raise 'error', e, type(e)
      say e, z
      return z

    # Do Special Forms before evaling the args.
    h, t = x[0], x[1:]
    switch h:
      case 'lambda':
        return x
      case 'if': 
        if len(t) != 3:
          raise 'Bad if statement, got %d args, wanted 3' % len(t)
        tcond = evalIt(t[0])
        say t[0], tcond
        cond = float(tcond)
        if cond == 0.0:
          return evalIt(t[2])
        else:
          return evalIt(t[1])

    # Eval each arg.
    # TODO: evalIt
    #subx = [(.Eval(RelativeTo(e[1:], dpath), depth, env) if (type(e) is str and e.startswith('$')) else e) for e in x]
    subx = [evalIt(e) for e in x]

    h, t = subx[0], subx[1:]

    if type(h) is tuple:
      if len(h) != 3:
        raise 'Bad tuple as command, expected length 3: %v' % h
      h1, h2, h3 = h
      if h1 != 'lambda':
        raise 'Bad lambda expression, expected first is "lambda": %v' % h
      if type(h2) is not tuple:
        raise 'Bad lambda expression, expected second is tuple: %v' % h
      if type(h3) is not tuple:
        raise 'Bad lambda expression, expected third is tuple: %v' % h
      nvar = len(h2)
      narg = len(t)
      if nvar != narg:
        raise 'In applying lambda, bad number of args, got %d expected %d: %v' % (narg, nvar, x)
      env2 = [] + env
      for var, val in zip(h2, t):
        env2 = [(var, val)] + env2
        return .EvalTuple(h3, path, depth+1, env2)

    switch h:
      case '++':
        return ''.join(list(t))
      case '+':
        return NumStr(sum([float(e) for e in t]))
      case '*':
        return NumStr(reduce(lambda a, b: float(a)*float(b), t, 1.0))
      case '-':
        must len(t) == 2
        return NumStr(float(t[0]) - float(t[1]))
      case '==':
        must len(t) == 2
        return BoolStr(t[0] == t[1])
      case '<':
        must len(t) == 2
        return BoolStr(float(t[0]) < float(t[1]))
    raise 'bad command %q' % h

def NumStr(x):
  return '%.18g' % x
def BoolStr(x):
  return '1' if x else '0'

pass

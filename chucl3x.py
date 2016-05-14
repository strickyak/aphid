# Chucl lisp-like interpreter for laph3
#
# t = Chucl(engine)
#   where engine is Laph3 CompileX().
#
#   str: A final str value.
#   set: A directory node, listing its keys.
#   list: A chucl expression to be evaluated.

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
  def __init__(engine):
    .engine = engine

  def EvalPath(path, depth=0, env=None):
    if env:
      # First look in the env for the path.
      for k, v in env:
        if k == path:
          return v

    if depth > 100:
      raise 'EvalPath: too deep in path %q' % path
    try:
      x = .engine.Resolve(path)
    except as ex:
      raise 'EvalPath: exception in resolving path %q: %s' % (path, str(ex))

    say path, depth, env, x
    z = .Evaluate(x, path, depth, env)
    say path, depth, env, x, z
    return z

  def Evaluate(x, path, depth, env):
    say x, path, depth, env
    if path.find('flags/flags') >= 0:
      raise 'OHNOOOOOOO', path
    depth += 1
    if x is None:
      raise 'Evaluate: got None for path %q' % path
    if depth > 100:
      raise 'Evaluate: too deep in path %q' % path

    switch type(x):
      case str:
        return x
      case set:
        z = {}
        for e in x:
            if e.startswith('_'): continue  # In Chucl, don't return _* slots in objects.
            try:
              r = .EvalPath(J(path, e), depth+1, env)
              z[e] = r
            except as ex:  # TODO
              # GIVE UP and leave the original there.
              z[e] = ('bad: cannot EvalPath', path, e, J(path, e), ex)
        return z

      case list:
        return .Apply(x, path, depth+1, env)
      default:
        raise 'Evaluate path %q: bad type %q in %v' % (path, type(x), x)
    raise 'NOTREACHED'

  def Apply(x, path, depth, env):
    say (x, path, depth, env)
    dpath = D(path)
    depth += 1

    def evaluate(e):
      return .Evaluate(e, path, depth+1, env)

    # Do Special Forms before evaling the args.
    h, t = x[0], x[1:]
    switch h:
      case 'lambda':
        return x
      case 'if': 
        if len(t) != 3:
          raise 'Bad if statement, got %d args, wanted 3' % len(t)
        tcond = evaluate(t[0])
        say t[0], tcond
        cond = float(tcond)
        if cond == 0.0:
          return evaluate(t[2])
        else:
          return evaluate(t[1])

    # Evaluate each arg.
    subx = [evaluate(e) for e in x]

    h, t = subx[0], subx[1:]

    if type(h) is list:
      if len(h) != 3:
        raise 'Bad list as lambda expression, expected length 3: %v' % h
      h1, h2, h3 = h
      if h1 != 'lambda':
        raise 'Bad lambda expression, expected first is "lambda": %v' % h
      if type(h2) is not list:
        raise 'Bad lambda expression, expected second is list: %v' % h
      if type(h3) is not list:
        raise 'Bad lambda expression, expected third is list: %v' % h
      nvar = len(h2)
      narg = len(t)
      if nvar != narg:
        raise 'In applying lambda, bad number of args, got %d expected %d: %v' % (narg, nvar, x)
      env2 = [] + env
      for var, val in zip(h2, t):
        env2 = [(var, val)] + env2
        return .Apply(h3, path, depth, env2)

    switch h:
      case 'bad':
        raise x
      case 'error':
        raise list(['bad'] + t)
      case '++':
        return ''.join(list(t))
      case '+':
        return NumStr(sum([float(e) for e in t]))
      case '*':
        return NumStr(reduce(lambda a, b: float(a)*float(b), t, 1.0))
      case '-':
        must len(t) == 2, t
        return NumStr(float(t[0]) - float(t[1]))
      case '==':
        must len(t) == 2, t
        return BoolStr(t[0] == t[1])
      case '!=':
        must len(t) == 2, t
        return BoolStr(t[0] != t[1])
      case '<':
        must len(t) == 2, t
        return BoolStr(float(t[0]) < float(t[1]))
      case '<=':
        must len(t) == 2, t
        return BoolStr(float(t[0]) <= float(t[1]))
      case '>':
        must len(t) == 2, t
        return BoolStr(float(t[0]) > float(t[1]))
      case '>=':
        must len(t) == 2, t
        return BoolStr(float(t[0]) >= float(t[1]))
      case 'len':
        must len(t) == 1, t
        return str(len(t[0]))
      case 'map':
        must len(t) == 2, t
        return [.Apply((t[0], e), path, depth, env) for e in t[1]]
      case 'filter':
        must len(t) == 2, t
        return [e for e in t[1] if float(.Apply((t[0], e), path, depth, env))]
      case 'list':
        return [e for e in t]
      case 'sorted':
        must len(t) == 1, t
        must type(t[0]) == list
        return [e for e in sorted(t)]
      case 'get':
        var, = t

        if env:
          # First look in the env for the var.
          for ek, ev in env:
            if ek == var:
              return ev

        dpath = D(path)
        say 'AbsolutePathRelativeTo <<<', var, dpath
        resolved = .engine.AbsolutePathRelativeTo(var, dpath)
        say 'AbsolutePathRelativeTo >>>', var, dpath, resolved
        say var, dpath, resolved
        z = .EvalPath(resolved, depth, env)
        say x, path, dpath, z
        return z
      case 'dget':
        must len(t) == 2, t
        thing, key = t
        switch type(thing):
          case dict:
            return .Evaluate(thing[key], J(path, key), depth, env)
          case list:
            return .Evaluate(thing[int(key)], J(path, key), depth, env)
          case str:
            return .Evaluate(thing[int(key)], J(path, key), depth, env)
      case 'keys':
        must len(t) == 1, t
        must type(t[0]) == dict
        return sorted(t[0].keys())
      case 'values':
        must len(t) == 1, t
        must type(t[0]) == dict
        return list(t[0].values())  # Values may not sort.
      case 'items':
        must len(t) == 1, t
        must type(t[0]) == dict
        return sorted(t[0].items())
    raise 'bad command %q' % h

def NumStr(x):
  return '%.18g' % x
def BoolStr(x):
  return '1' if x else '0'

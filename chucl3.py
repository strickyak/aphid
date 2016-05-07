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
    def recurse(d, p, here):
      if not p: return d
      h, t = HT(p)
      dh = d.get(h, None)
      if dh is None:
        raise 'Find: cannot find key %q in path %q' % (h, path)
      if t and type(dh) is dict:
        return recurse(dh, t, J(here, h))
      if t and type(dh) is str and dh.startswith('$'):
        adh = .ResolveRel(dh[1:], here)
        return .Find(J(adh, t))
      if t:
        raise 'Find: cannot use tail key %q in object %s in path %q' % (t, repr(dh), path)
      return dh
    return recurse(.tree, path, '/')

  def ResolveRel(path, rel):
    hp = H(path)

    if path.startswith('/'):
      rel2 = '/'
    else:
      rel2 = rel

    prev = None
    while True:
      hpr = RelativeTo(hp, rel2)
      say hpr, hp, rel2, (path, rel)

      dt = .tree
      for e in S(hpr):
        dt = dt.get(e)
        if dt is None: break

      if dt is not None:
        return RelativeTo(path, rel2)

      rel2 = D(rel2)
      #if rel2 == '.' or rel2 == '':
      #  raise 'ResolveRel: failed to resolve %q starting at %q' % (hp, rel)
      if prev in ['/', '.', '']:
        raise 'ResolveRel: failed to resolve %q starting at %q' % (hp, rel)
      prev = rel2

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

    say path, depth, env, x
    z = .Resolve(x, path, depth, env)
    say path, depth, env, x, z
    return z

  def Resolve(x, path, depth, env):
    depth += 1
    if x is None:
      raise 'Eval: got None for Eval path %q' % path
    if depth > 100:
      raise 'Resolve: too deep in path %q' % path

    switch type(x):
      case str:
        if x.startswith('$'):
          varpath = x[1:]

          if env:
            # First look in the env for the varpath.
            for ek, ev in env:
              if ek == varpath:
                return ev

          dpath = D(path)
          resolved = .ResolveRel(varpath, dpath)
          say varpath, dpath, resolved
          z = .Eval(resolved, depth, env)
          say x, path, dpath, z
          return z
        say x, path
        return x
      case list:
        return x
      case dict:
        # When it's a dict, we might need to Resolve all its members.
        z = dict([(k, .Resolve(v, J(path, k), depth+1, env)) for k, v in x.items() if not k.startswith('_')])
        return z
      case tuple:
        return .Apply(x, path, depth+1, env)
    raise 'Eval path %q: bad type %q in %v' % (path, type(x), x)

  def Apply(x, path, depth, env):
    say (x, path, depth, env)
    dpath = D(path)
    depth += 1

    def resolve(e):
      return .Resolve(e, path, depth+1, env)

    # Do Special Forms before evaling the args.
    h, t = x[0], x[1:]
    switch h:
      case 'lambda':
        return x
      case 'if': 
        if len(t) != 3:
          raise 'Bad if statement, got %d args, wanted 3' % len(t)
        tcond = resolve(t[0])
        say t[0], tcond
        cond = float(tcond)
        if cond == 0.0:
          return resolve(t[2])
        else:
          return resolve(t[1])

    # Eval each arg.
    subx = [resolve(e) for e in x]

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
        return .Apply(h3, path, depth, env2)

    switch h:
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
        must len(t) == 2, t
        thing = t[0]
        key = t[1]
        switch type(thing):
          case dict:
            return .Resolve(thing[key], J(path, key), depth, env)
          case list:
            return .Resolve(thing[int(key)], J(path, key), depth, env)
          case tuple:
            return .Resolve(thing[int(key)], J(path, key), depth, env)
          case str:
            return .Resolve(thing[int(key)], J(path, key), depth, env)
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

pass

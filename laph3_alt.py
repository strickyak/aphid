from . import laph3 as L

NONE = ()

class AltVisitor:
  def __init__(compiled):
    .compiled = compiled
    .top = .compiled.tree
    .mem = {}

  def visitTuple(p, here, togo):
    # dic
    h, t = L.HT(togo)
    if not h:
      # Return tuple keys.
      return set(p.dic.keys())

    hereH = L.J(here, h)
    x = p.dic.get(h, NONE)
    say p.dic
    say here, togo, h, t, x
    if x is NONE:
      return ('bad', 'visitTuple cannot find %q in %q' % (h, here))
    
    return x.visit(self, here=hereH, togo=t)
        
  def visitDerive(p, here, togo):
    # template, diff

    d = .LookupDir(p.template, L.D(here))
    absT = L.J(d, p.template)

    h, t = L.HT(togo)
    tem = .EvalPath(absT)
    must type(tem) is set, tem, absT, here, togo
    if not h:
      # Return derived tuple keys.
      return set(tem | set(p.diff.keys()))  # Union template & diff keys.

    hereH = L.J(here, h)
    x = p.diff.get(h, NONE)
    if x is NONE:
      z = .EvalPath(L.J(absT, h, t))
      say here, togo, z
      return z
    
    z = x.visit(self, here=hereH, togo=t)
    say here, togo, z
    return z

  def visitEnhance(p, here, togo):
    # dslot, diff
    raise 'TODO'

  def visitBare(p, here, togo):
    must not togo, here, togo
    .mem[here] = p.a
    return p.a

  def visitCommand(p, here, togo):
    raise 'TODO'

  def EvalPath(path):
    return .visitTuple(.top, here='/', togo=path)
    
  def LookupDir(path, cwd):
    if path.startswith('/'):
      return '/'

    vec = L.S(path)
    if not vec:  raise 'No valid path: %q' % path
    hd = vec[0]

    say hd, path, cwd
    d = cwd
    prev = None
    while prev not in ['/', '', '.']:
      try:
        say path, cwd, d
        x = .EvalPath(L.J(d, hd))
        say path, cwd, d, x
        if x is not None:
          return d
      except as ex:
        say path, cwd, d, ex
        pass
      prev = d
      d = L.D(d)
    raise 'Path %q not found in or above directory %q' % (path, cwd)

################################

t1 = L.Compile(`
  a = bilbo
  b = {
    c = {
      d = frodo
    }
    e = {
      d = samwise
    }
  }
`)

av1 = AltVisitor(t1)
must av1.EvalPath('/') == set(['a', 'b'])
must av1.EvalPath('/a') == 'bilbo'
must av1.EvalPath('/b') == set(['c', 'e'])
must av1.EvalPath('/b/c') == set(['d'])
must av1.EvalPath('/b/c/d') == 'frodo'

################################

t2 = L.Compile(`
  Q = { a = 111 ; b = 222 }
  R = Q { a = 777 ; c = 888}
`)

av2 = AltVisitor(t2)
must av2.EvalPath('/') == set(['Q', 'R'])
must av2.EvalPath('/Q') == set(['a', 'b'])
must av2.EvalPath('/R') == set(['a', 'b', 'c'])
must av2.EvalPath('/Q/a') == '111'
must av2.EvalPath('/Q/b') == '222'
must av2.EvalPath('/R/a') == '777'
must av2.EvalPath('/R/b') == '222'
must av2.EvalPath('/R/c') == '888'

################################

t3 = L.Compile(`
  X = {
    M = { a = 111 ; b = 222 }
    N = { c = 333 ; d = 444 }
  }
  Y = X {
    P = { z = 888 }
  }
`)

av3 = AltVisitor(t3)
must av3.EvalPath('/') == set(['X', 'Y'])
must av3.EvalPath('/X') == set(['M', 'N'])
must av3.EvalPath('/Y') == set(['M', 'N', 'P'])


################################

print 'OKAY laph3_alt.py'

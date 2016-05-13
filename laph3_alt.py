from . import laph3 as L

NONE = ()

def Spaces(n):
  if n > 20:
    raise 'TOO DEEP'
  return '\n\n' + (n * ' * ')

class AltVisitor:
  def __init__(compiled):
    .compiled = compiled
    .top = .compiled.tree
    .mem = {}

  def visitTuple(p, here, togo, shadow, real, stops, depth):
    print '%s visitTuple <<< %s [[ %s ]] %s || %s' % (Spaces(depth), here, togo, shadow, real)
    say here, togo, shadow, real, stops
    # dic
    h, t = L.HT(togo)
    if not h:
      # Return tuple keys.
      z = set(p.dic.keys())
      print '%s visitTuple >>> %s' % (Spaces(depth), repr(z))
      return z

    hereH = L.J(here, h)
    x = p.dic.get(h, NONE)
    say p.dic
    say here, togo, real, h, t, x
    if x is NONE:
      return ('bad', 'visitTuple cannot find %q in %q' % (h, here))

    shadowH = L.J(shadow, h) if shadow else shadow
    realH = L.J(real, h) if real else real
    say hereH, t, shadowH, realH, stops
    z = x.visit(self, here=hereH, togo=t, shadow=shadowH, real=realH, stops=stops, depth=depth+1)
    print '%s visitTuple >>> %s' % (Spaces(depth), repr(z))
    return z

  def visitDerive(p, here, togo, shadow, real, stops, depth):
    print '%s visitDerive %s <<< %s [[ %s ]] %s || %s' % (Spaces(depth), p.template, here, togo, shadow, real)
    # template, diff

    #d, n = .LookupDir(p.template, L.D(here))
    absD, n = .LookupDir(p.template, L.D(real), depth=depth+1)
    absT = L.J(absD, p.template)
    say absT, n, p.template, real, L.D(real)

    h, t = L.HT(togo)
    say absT
    tem = .EvalPath(absT, depth=depth+1)
    say absT, tem
    must type(tem) is set, tem, absT, here, togo
    if not h:
      # Return derived tuple keys.
      z = set(tem | set(p.diff.keys()))  # Union template & diff keys.
      say z
      print '%s visitDerive >>> %s' % (Spaces(depth), repr(z))
      return z

    say h
    hereH = L.J(here, h)
    realH = L.J(real, h) if real else real
    x = p.diff.get(h, NONE)
    say h, hereH, realH, x, x is NONE
    if x is NONE:
      z = .EvalPath(L.J(absD, h, t), real=real, depth=depth+1)  # Add real path.
      say here, togo, z
      print '%s visitDerive >>> %s' % (Spaces(depth), repr(z))
      return z

    # Shadow begins here, when we go down the diff path.
    z = x.visit(self, here=hereH, togo=t, shadow=L.J(absD, h), real=realH, stops=stops, depth=depth+1)
    say here, togo, z
    print '%s visitDerive >>> %s' % (Spaces(depth), repr(z))
    return z

  def visitEnhance(p, here, togo, shadow, real, stops, depth):
    print '%s visitEnhance %s <<< %s [[ %s ]] %s || %s' % (Spaces(depth), p.dslot, here, togo, shadow, real)
    # dslot, diff
    h, t = L.HT(togo)
    say here, togo, shadow, real, stops, h, t
    if not h:
      # Just the enhanced directory.
      enhancedSet = set(p.diff.keys())
      shadowSet = .EvalPath(shadow, real, stops=stops, depth=depth+1)
      say here, togo, shadow, real, stops
      say enhancedSet
      say shadowSet
      must type(shadowSet) is set
      z = enhancedSet | shadowSet  # Union.
      print '%s visitEnhance >>> %s' % (Spaces(depth), repr(z))
      return z

    hereH = L.J(here, h)
    realH = L.J(real, h) if real else real
    x = p.diff.get(h, NONE)
    if x is NONE:
      z = .EvalPath(L.J(shadow, h, t), real=real, depth=depth+1)
      say here, togo, shadow, h, t, z
      print '%s visitEnhance >>> %s' % (Spaces(depth), repr(z))
      return z

    z = x.visit(self, here=hereH, togo=t, shadow=L.J(shadow, h), real=realH, stops=stops, depth=depth+1)
    say here, togo, shadow, h, t, z
    print '%s visitEnhance >>> %s' % (Spaces(depth), repr(z))
    return z

  def visitBare(p, here, togo, shadow, real, stops, depth):
    must not togo, here, togo
    .mem[here] = p.a
    return p.a

  def visitCommand(p, here, togo, shadow, real, stops, depth):
    raise 'TODO'

  def EvalPath(path, shadow=None, stops=None, real=None, depth=0):
    # Start with the path as real.
    real2 = real if real else '/'
    say path, shadow, stops, real
    z = .visitTuple(.top, here='/', togo=path, shadow=shadow, real=real2, stops=stops, depth=depth+1)
    say path, shadow, stops, real, z
    return z

  def LookupDir(path, cwd, depth=0):
    if path.startswith('/'):
      return '/', None

    vec = L.S(path)
    if not vec:  raise 'No valid path: %q' % path
    hd = vec[0]

    say hd, path, cwd
    d = cwd
    prev = None
    n = 0
    while prev not in ['/', '', '.']:
      try:
        say path, cwd, d
        x = .EvalPath(L.J(d, hd), depth=depth+1)
        say path, cwd, d, x
        if x is not None:
          return d, n
      except as ex:
        say path, cwd, d, ex
        pass
      prev = d
      d = L.D(d)
      n += 1
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
    M { a = 555 ; f = 666 }
    P = { z = 888 }
  }
`)

av3 = AltVisitor(t3)
must av3.EvalPath('/') == set(['X', 'Y'])
must av3.EvalPath('/X') == set(['M', 'N'])
must av3.EvalPath('/Y') == set(['M', 'N', 'P'])
must av3.EvalPath('/X/M/a') == '111'
must av3.EvalPath('/X/M/b') == '222'
must av3.EvalPath('/X/N/c') == '333'
must av3.EvalPath('/X/N/d') == '444'

must av3.EvalPath('/Y/M') == set(['a', 'b', 'f'])
must av3.EvalPath('/Y/M/a') == '555'
must av3.EvalPath('/Y/M/b') == '222'
must av3.EvalPath('/Y/M/f') == '666'
must av3.EvalPath('/Y/N/d') == '444'
must av3.EvalPath('/Y/P/z') == '888'

################################

t4 = L.Compile(`
  OLD = {
    info = { age = old }
    P = info { size = small }
    Q = P { size = medium }
  }
  NEW = OLD {
    info { age = new }
  }
`)

av4 = AltVisitor(t4)
must av4.EvalPath('/NEW/P/size') == 'small'
must av4.EvalPath('/NEW/P/age') == 'new'

################################

print 'OKAY laph3_alt.py'

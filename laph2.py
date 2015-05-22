from go import path as P, regexp

Special = regexp.MustCompile('^[][{}()=]$').FindString

class Lex:
  def __init__(program):
    .program = program
    .toks = .lexProgram()
    
  def lexLine(line):
    return [x for x in line.split() if x]

  def lexProgram():
    z = []
    i = 1
    for line in .program.split('\n'):
      z += [(x, i) for x in .lexLine(line) + [';']]
      i += 1
    return z


class Node:
  def __init__(e, name, up, sup):
    .e = e
    .name = name
    .up = up
    .sup = sup

class LazyEval:
  def __init__(root):
    .root = root
    .memo = {}

  def Eval(path, origin='/'):
    if not path.startswith('/'):
      path = P.Join('/', origin, path)
      return .Eval(path)

    say 'Eval:', (path, origin)
    steps = [x for x in path.split('/') if x]

    return .root.visit(self, past=[], future=steps)

  def visitShadow(p, past, future, **kw):
    past, future = past.copy(), future.copy()
    say 'visitShadow:', past, future, p.name, kw
    sup = kw.get('sup')
    must sup, 'Cannot shadow if not derived', past, future, p.name, kw

    if future:  # Going through us.
      x = future[0]
      if x in p.diff.dic:  # First try the local diffs.
        x = future.pop(0)
        past.append(x)

        say 'Shadow/Uno', past, x, future
        ret = p.diff.dic[x].visit(self, past=past, future=future, sup=P.Join(sup, x))
        say ret
        return ret
      else:
        ret = .Eval(P.Join(sup, x), P.Join('/', *past))
        say ret
        return ret
        
    else: # Terminating here.  Return list of things.
      sup = kw.get('sup')
      say 'Shadow/Tres', past, sup
      must sup, (past, sup)
      say sup, P.Join('/', *past)
      subs = .Eval(sup, P.Join('/', *past))
      say subs
      z = dict([(e, True) for e in subs])
      say z

      say p.diff.dic
      for k in p.diff.dic:
        z[k] = True
      return sorted(z.keys())

  def visitDerive(p, past, future, **kw):
    past, future = past.copy(), future.copy()
    say 'visitDerive:', past, future, p.name, kw

    if future:  # Going through us.
      x = future[0]
      if x in p.diff.dic:  # First try the local diffs.
        x = future.pop(0)
        past.append(x)

        say 'Derive/Uno', past, x, future, p.template
        ret = p.diff.dic[x].visit(self, past=past, future=future, sup=P.Join(p.template, x))
        say ret
        return ret
      else:
        say 'Derive/Dos', p.template, future, past
        ret = .Eval(P.Join(p.template, *future), P.Join('/', *past))
        say ret
        return ret
        
    else: # Terminating here.  Return list of things.
      sup = .Eval(p.template, P.Join('/', *past))
      must type(sup) is list, (p.template, P.Join('/', *past))
      z = dict([(e, True) for e in sup])

      for k in p.diff.dic:
        z[k] = True
      return sorted(z.keys())

  def visitTuple(p, past, future, **kw):
    past, future = past.copy(), future.copy()
    if future:
      x = future.pop(0)
      past.append(x)
      say past, x, future
      y = p.dic.get(x)
      if y:
        return y.visit(self, past=past, future=future)
      else:
        raise "Ain't no %q in Tuple %q" % (x, past)
    else:
      return sorted(p.dic.keys())
        
  def visitBare(p, past, future, **kw):
    if future:
        raise "Ain't no %q in Scalar %q" % (future, past)
    else:
      return p.a

def Find(k, local, root):
  p = root if k.startswith('/') else local
  for x in k.split('/'):
    switch x:
      case '':
        pass
      case '_up':
        p = p.up
      case '_super':
        p = p.sup
      default:
        p = p.find(x)
  return p

class Derive:  # Derive from a tuple.
  def __init__(template, diff):
    .template = template
    .base = None
    .diff = diff
    .dic = {}
    .name = None
    .up = None
    .root = None
    .sup = None
  def visit(w, **kw):
    return w.visitDerive(self, **kw)
  def find(k):
    if k in .dic:
      return .dic[k]
    else:
      raise 'Cannot find slot %q in Tuple %q' % (k, .name)
  def __str__():
    return '(Derive(%q): %v)' % (.template, .diff)

class Shadow:  # Derive from a tuple.
  def __init__(dslot, diff):
    .dslot = dslot
    .diff = diff
    .name = None
  def visit(w, **kw):
    return w.visitShadow(self, **kw)
  def __str__():
    return '(Shadow(%q): %v)' % (.dslot, .diff)

class Tuple: # Named tuple with {...}.
  def __init__(dic):
    .dic = dic
    .name = None
    .up = None
    .root = None
    .sup = None
  def visit(w, **kw):
    return w.visitTuple(self, **kw)
  def find(k):
    if k in .dic:
      return .dic[k]
    else:
      raise 'Cannot find slot %q in Tuple %q' % (k, .name)
  def __str__():
    return '{"%s" %s }' % (str(.name), ' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))
  def __repr__():
    return '{"%s" %s }' % (str(.name), ' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))
class Dollar: # Dollar substituted bareword.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitDollar(self, **kw)
  def __str__():
    return '$%v' % .a
class Bare:  # Bareword has its own value.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitBare(self, **kw)
  def __str__():
    return '%v' % .a
class Parens:  # Parenthesized evaluation.
  def __init__(vec):
    .vec = vec
  def visit(w, **kw):
    return w.visitParens(self, **kw)
  def __str__():
    return '( %v )' % .a

class Parse:
  def __init__(program):
    .program = program
    .lex = Lex(program)
    .p = .lex.toks
    .i = 0
    .d = 0

  def next():
    .i += 1
    print 'NEXT{{{ %v }}}' % .p[.i]

  def expr():
    .d += 1
    say '<<<', (.d, .i), .p[.i]
    z = .expr2()
    say '>>>', (.d, .i), .p[.i], str(z)
    .d -= 1
    return z
  def expr2():
    x, xl = .p[.i]
    .next()
    if Special(x):
      switch x:
        case '(':
          z = []
          while .p[.i][0] != ')':
            z.append(.expr())
          return Parens(z)
        case '{':
          d = {}
          while .p[.i][0] != '}':
            k, kl = .p[.i]
            .next()
            if k == ';':
              continue
            must not Special(k)

            op, ol = .p[.i]
            must Special(op), k, op, kl, ol
            switch op:
              case '=':
                .next()
                val = .expr()
                d[k] = val
              case '{':
                tup = .expr()
                must type(tup) is Tuple
                d[k] = Shadow(k, tup)  # TODO
          # end while
          .next()
          return Tuple(d)
        default:
          raise str(('Default', x, .i, .p[.i]))

    else: # if not Special
      peek, peekl = .p[.i]
      if peek == ';' or peek == '}':
        if x.startswith('$'):
          return Dollar(x)
        else:
          return Bare(x)
      elif peek == '{':
        tup = .expr()
        must type(tup) is Tuple
        return Derive(x, tup)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]

pass

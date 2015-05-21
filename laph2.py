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

class Pass1:
  """Pass1 sets names on the nodes."""
  def visitDerive(q, **kw):
    q.name = kw['name']
    q.up = kw['up']
    q.root = kw['root']
    q.diff.name = kw['name']
    q.diff.up = kw['up']
    q.diff.root = kw['root']
    for k, v in sorted(q.diff.dic.items()):
      kw2 = kw.copy()
      kw2['name'] = P.Join(kw['name'], k)
      kw2['up'] = self
      v.visit(self, **kw2)
  def visitTuple(q, **kw):
    q.name = kw['name']
    q.up = kw['up']
    q.root = kw['root']
    for k, v in sorted(q.dic.items()):
      kw2 = kw.copy()
      kw2['name'] = P.Join(kw['name'], k)
      kw2['up'] = self
      v.visit(self, **kw2)
  def visitDollar(q, **kw):
    pass
  def visitBare(q, **kw):
    pass
  def visitParens(q, **kw):
    pass

class Pass2:
  """Pass2 copies derived dictionaries."""
  def visitDerive(q, **kw):
    say q.name
    for kk, ww in sorted(kw.items()):
      say kk, ww
    if q.dobj:
      base = Find(q.dobj, q, q.root)
      say base
    else:
      base = kw['sup'].dic.get(q.dslot) if kw['sup'] else None
      say base
    q.base = base
    say q.base

    q.dic = {}
    if base.dic:
      for k, v in sorted(base.dic.items()):
      TODO -- derive if Tuple?
    
    say q.dic
    q.dic.update(q.diff.dic)
    say q.dic
    q.sup = base # TODO -- null _supper?

    for k, v in sorted(q.dic.items()):
      say k, v
      kw2 = kw.copy()
      kw2['name'] = P.Join(kw['name'], k)
      kw2['up'] = False
      kw2['sup'] = base.dic.get(k) if base else None
      say k, v, kw
      v.visit(self, **kw2)
  def visitTuple(q, **kw):
    kwsup = kw['sup']
    for k, v in sorted(q.dic.items()):
      if k == '_up' or k == '_super':
        continue
      kw2 = kw.copy()
      kw2['up'] = False
      kw2['name'] = P.Join(kw['name'], k)
      kw2['sup'] = kwsup.dic.get(k) if kwsup else None
      v.visit(self, **kw2)
  def visitDollar(q, **kw):
    pass
  def visitBare(q, **kw):
    pass
  def visitParens(q, **kw):
    pass

class Eval:
  def visitDerive(q, **kw):
    return dict([(k, v.visit(self, **kw)) for k, v in sorted(q.dic.items()) if not k.startswith('_')])
  def visitTuple(q, **kw):
    return dict([(k, v.visit(self, **kw)) for k, v in sorted(q.dic.items()) if not k.startswith('_')])
  def visitDollar(q, **kw):
    return '$' + q.a
  def visitBare(q, **kw):
    return q.a
  def visitParens(q, **kw):
    return str(q.vec)

def Name(p):
  return p.name if p else '<None>'

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
  def __init__(dobj, dslot, diff):
    .dobj = dobj
    .dslot = dslot
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
    return '(Derive(%q): %v)' % (.dobj if .dobj else "~" + .dslot, .diff)
  #def __repr__():
  #  return '(Derive(%q): %v)' % (.dobj if .dobj else "~" + .dslot, .diff)
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
                d[k] = Derive(None, k, tup)  # TODO
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
        return Derive(x, None, tup)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]

pass

from go import path as P, regexp

MAX_DELEGATION = 2  # Awful hack.  Should get feedback, if things fail.

class Compile:
  def __init__(program):
    .program = program
    .tree = Parse(program).expr()
    must type(.tree) == Tuple, 'Expected program to be a Tuple, but got %q' % type(.tree)
    .src, .dst = {}, {}

    sv = SrcVisitor(.src)
    num_levels = 1 + .tree.visit(sv, path='/')

    dv = DstVisitor(.src, .dst)
    for level in range(num_levels + MAX_DELEGATION):
      .tree.visit(dv, spath='/', dpath='/', desired=level, level=0)

  def Eval(path):
    path = C(path)
    return DstEval(.dst, path)

  def Keys(path):
    path = C(path)
    d = DstEval(.dst, path)
    return sorted([k for k in d if not k.startswith('_')])

###############################
# Regular Expression Functions
Special = regexp.MustCompile('^[][{}()=]$').FindString
ReplaceGroupersAnywhere = regexp.MustCompile('([][{}()])').ReplaceAllString

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

###############################
# Lexical Analysis:
#   -- Add spaces arund Groupers ( ) [ ] { }.
#   -- split lines on white space.
#   -- Add ';' to end of every line.
#   -- Return list of token tuples (value, lineno).
class Lex:
  def __init__(program):
    .program = ReplaceGroupersAnywhere(program, ' $1 ')
    say .program
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

###############################
# Abstract Syntax Tree Nodes

class Derive:  # Enhance a derived subtuple.
  def __init__(template, diff):
    .template = template
    .diff = diff
    .dic = {}
  def visit2(w, **kw):
    return w.visit2Derive(self, **kw)
  def visit(w, **kw):
    return w.visitDerive(self, **kw)
  def find(k):
    if k in .dic:
      return .dic[k]
    else:
      raise 'Cannot find slot %q in Tuple %q' % (k, str(self))
  def __str__():
    return '(Derive(%q): %v)' % (.template, .diff)

class Enhance:  # Derive from a tuple.
  def __init__(dslot, diff):
    .dslot = dslot
    .diff = diff
  def visit2(w, **kw):
    return w.visit2Enhance(self, **kw)
  def visit(w, **kw):
    return w.visitEnhance(self, **kw)
  def __str__():
    return '(Enhance(%q): %v)' % (.dslot, .diff)

class Tuple: # Named tuple with {...}.
  def __init__(dic):
    .dic = dic
  def visit2(w, **kw):
    return w.visit2Tuple(self, **kw)
  def visit(w, **kw):
    return w.visitTuple(self, **kw)
  def find(k):
    if k in .dic:
      return .dic[k]
    else:
      raise 'Cannot find slot %q in Tuple %q' % (k, str(self))
  def __str__():
    return '{ %s }' % (' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))
  def __repr__():
    return '{ %s }' % (' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))

class Dollar: # Dollar substituted bareword.
  def __init__(a):
    .a = a
  def visit2(w, **kw):
    return w.visit2Dollar(self, **kw)
  def visit(w, **kw):
    return w.visitDollar(self, **kw)
  def __str__():
    return '<$%v>' % .a

class Bare:  # Bareword has its own value.
  def __init__(a):
    .a = a
  def visit2(w, **kw):
    return w.visit2Bare(self, **kw)
  def visit(w, **kw):
    return w.visitBare(self, **kw)
  def __str__():
    return '<%v>' % .a

class Command:  # Parenthesized command.
  def __init__(vec):
    .vec = vec
  def visit2(w, **kw):
    return w.visit2Command(self, **kw)
  def visit(w, **kw):
    return w.visitCommand(self, **kw)
  def __str__():
    return '<( %v )>' % .vec

###############################
# The Parser.
#  -- Lexes the program.
#  -- Converts into Abstract Syntax Tree.

class Parse:
  def __init__(program):
    .program = program
    .lex = Lex(program)
    .p = .lex.toks
    .i = 0
    .d = 0

  def next():
    .i += 1

  def command():
    z = []
    while .p[.i][0] != ')':
      word, wordl = .p[.i]
      must not Special(word), word
      if word.startswith('$'):
        z.append( Dollar(word[1:]) )
      else:
        z.append( Bare(word) )
      .next()
    .next()
    return Command(z)

  def tuple():
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
          d[k] = Enhance(k, tup)  # TODO
    # end while
    .next()
    return Tuple(d)

  def expr():
    .d += 1
    #say '<<<', (.d, .i), .p[.i]
    z = .expr2()
    #say '>>>', (.d, .i), .p[.i], str(z)
    .d -= 1
    return z

  def expr2():
    x, xl = .p[.i]
    .next()
    if Special(x):
      switch x:
        case '(':
          return .command()
        case '{':
          return .tuple()
        default:
          raise str(('Default', x, .i, .p[.i]))

    else: # if not Special
      peek, peekl = .p[.i]
      if peek == ';' or peek == '}':
        if x.startswith('$'):
          return Dollar(x[1:])
        else:
          return Bare(x)
      elif peek == '{':
        tup = .expr()
        must type(tup) is Tuple
        return Derive(x, tup)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]


###############################
# Nested Dictionary Utilities.

def Make(dic, *vec):
  p = dic
  for k in vec:
    if k not in p:
      p[k] = {}
    p = p[k]

def Set(value, dic, *vec):
  p = dic
  for k in vec[:-1]:
    if k not in p:
      p[k] = {}
    p = p[k]
  k = vec[-1]
  p[k] = value

def Get(dic, *vec):
  p = dic
  for k in vec:
    p = p[k]
  return p

###############################
# Evaluators

def DstEval(dst, path, rel='/'):
  path = R(path, rel)
  say path
  p = dst.get(path)
  say sorted(dst.items())
  say sorted(dst.keys())
  must p, path
  switch type(p):
    case dict:
      return p
    case Bare:
      return p.a
    case Dollar:
      say p.a, path
      z = DstEval(dst, p.a, path)
      say z
      return z
    case Command:
      return ExecuteCommand(dst, p, D(path))

def ExecuteCommand(dst, p, path, **kw):
  vec = p.vec
  say vec, path
  must type(vec) is list
  cmd = vec[0]
  must type(cmd) is Bare, type(cmd), cmd
  cmd = cmd.a
  vec = vec[1:]

  # First look for special forms.
  switch cmd:
    case 'if':
      raise 'TODO'
    case 'fn':
      return p

  args = []
  for a in vec:
    say 'ARG:', a
    switch type(a):
      case Bare:
        say 'Bare', a.a
        args.append(a.a)
      case Dollar:
        say 'Dollar', a.a, path
        args.append(DstEval(dst, a.a, path))
      default:
        raise 'TODO', type(a), a, vec, path
    say 'ARGS:', args

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

###############################
# Destination & Source visitors.

class DstVisitor:
  def __init__(src, dst):
    .src = src  # Source tree to be made.
    .dst = dst  # Destination tree to be made.

  def visitTuple(p, spath, dpath, desired, level, **kw):
    say spath, dpath, kw, desired, level
    d = dict(__name__=dpath, __src__=spath)
    .dst[dpath] = d
    for k, v in sorted(p.dic.items()):
      say spath, dpath, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      v.visit(self, spath=spath2, dpath=dpath2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

  def visitDerive(p, spath, dpath, desired, level, **kw):
    template = R(p.template, D(spath))
    say spath, dpath, kw, template, desired, level
    d = dict(__name__=dpath, __src__=spath, __template__=p.template)
    .dst[dpath] = d
    level += 1
    if level > desired:
      return

    # TODO -- allow Derive & Enhance, as well as Tuple, as template.
    tp = .src.get(template)
    say tp, template

    if type(tp) is tuple:
      spath8, dpath8 = tp
      tp2 = .src.get(spath8)
      say tp, tp2, spath8, dpath8
      tp = tp2

    switch type(tp):
      case Tuple:
        must type(tp) == Tuple, 'Missing template %q for spath=%q dpath=%q, got %q' % (template, spath, dpath, repr(tp))
        dic = tp.dic
      case Derive:
        dic = tp.diff.dic
        dic = dict([(k9,v9) for k9, v9 in .dst.get(template).items() if not k9.startswith('__')])
      case Enhance:
        dic = tp.diff.dic
        dic = dict([(k9,v9) for k9, v9 in .dst.get(template).items() if not k9.startswith('__')])
      default:
        raise 'OH NO!', type(tp), tp

    # First the template.
    for k, v in sorted(dic.items()):
      say spath, dpath, template, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      sup2 = J(template, k)
      if type(v) is str:
        raise 'GOT STR', repr(v)
      while type(v) is tuple:
        spath8, dpath8 = v
        v = .src.get(spath8)
        if v is None:
          v = .dst.get(spath8)
      v.visit(self, spath=spath2, dpath=dpath2, sup=sup2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

    # Then the diffs.
    for k, v in sorted(p.diff.dic.items()):
      say spath, dpath, template, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      sup2 = J(template, k)
      v.visit(self, spath=spath2, dpath=dpath2, sup=sup2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

  def visitEnhance(p, spath, dpath, sup, desired, level, **kw):
    say spath, dpath, kw, desired, level
    d = dict(__name__=dpath, __src__=spath, __slot__=p.dslot)
    .dst[dpath] = d
    level += 1
    if level > desired:
      return

    say spath, dpath, kw, sup, desired, level

    td = .dst.get(sup)  # TODO
    if td:
      must type(td) == dict
      for k, v in sorted(td.items()):
        say spath, dpath, kw, sup, td, k, v, desired, level
        spath2 = J(spath, k)
        dpath2 = J(dpath, k)
        # TODO
        # v.visit(self, spath=spath2, dpath=dpath2)
        d[k] = (spath2, dpath2)

    # Then the diffs.
    for k, v in sorted(p.diff.dic.items()):
      say spath, dpath, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      v.visit(self, spath=spath2, dpath=dpath2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

  def visitBare(p, spath, dpath, desired, level, **kw):
    say spath, dpath, kw, desired, level
    .dst[dpath] = p

  def visitDollar(p, spath, dpath, desired, level, **kw):
    say spath, dpath, kw, desired, level
    .dst[dpath] = p

  def visitCommand(p, spath, dpath, desired, level, **kw):
    say spath, dpath, kw, desired, level
    .dst[dpath] = p


class SrcVisitor:
  """Make dictionary of source, and count depth of merging."""
  def __init__(src):
    .src = src  # Source tree to be made.

  def visitTuple(p, path, **kw):
    z = 0
    Make(.src, path)
    for k, v in sorted(p.dic.items()):
      path2 = J(path, k)
      Set(v, .src, path2)
      z = max(z, z + v.visit(self, path=path2))
    print '@@@', z, path
    return z

  def visitDerive(p, path, **kw):
    z = 1
    Make(.src, path)
    for k, v in sorted(p.diff.dic.items()):
      path2 = J(path, k)
      Set(v, .src, path2)
      z = max(z, z + v.visit(self, path=path2))
    print '@@@', z, path
    return z

  def visitEnhance(p, path, **kw):
    z = 1
    Make(.src, path)
    for k, v in sorted(p.diff.dic.items()):
      # p.dslot ?
      path2 = J(path, k)
      Set(v, .src, path2)
      z = max(z, z + v.visit(self, path=path2))
    print '@@@', z, path
    return z

  def visitBare(p, path, **kw):
    Set(p, .src, path)
    return 0

  def visitDollar(p, path, **kw):
    Set(p, .src, path)
    return 0

  def visitCommand(p, path, **kw):
    Set(p, .src, path)
    return 0

pass

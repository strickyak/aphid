from go import path as P, regexp, io/ioutil, strconv
from . import laph_chucl

MAX_DELEGATION = 2  # Awful hack.  Should get feedback, if things fail.

MATCH_INTEGER = regexp.MustCompile('^-?[0-9]+$').FindString

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

    def lookup_fn(k):
      #say k
      must k[0] == '/'
      b = B(k)
      d = D(k)
      # Look up the tree, until you find it.
      while True:
        x = J(d, b)
        if x in .dst:
          ret = .dst[x]
          #say k, ret
          return ret
        if d == '/':
          break
        d = D(d)  # Up to the parent directory.
      raise 'Cannot lookup %q', k
    .chucl = laph_chucl.Evaluator(lookup_fn, Command)

  def Eval(path):
    path = C(path)
    return .chucl.EvalPath(path)

  def Keys(path):
    path = C(path)
    d = .chucl.EvalPath(path)
    return sorted([k for k in d if not k.startswith('_')])

  def ToJson(path='/'):
    #say '@@1', path
    a = .Eval(path)
    #say '@@2', path, a
    switch type(a):
      case int:
        #say '@@3', 'int', a
        return repr(a)
      case float:
        #say '@@3', 'float', a
        return repr(a)
      case str:
        #say '@@3', 'str', a
        if MATCH_INTEGER(a):
          return a
        #try:
        #  n = strconv.ParseInt(a, 10, 32)
        #  return repr(n)
        #except:
        #  pass
        return repr(a)
      case list:
        #say '@@3', 'list', a
        vec = [.ToJson(J(path, e)) for e in a]
        #say '@@4', 'list', a, vec
        return '[%s]' % ','.join(vec)
      case dict:
        #say '@@3', 'dict', a
        vec = [(k, .ToJson(J(path, k))) for k, v in sorted(a.items()) if not k.startswith('_')]
        #say '@@4', 'dict', a, vec
        return '{%s}' % ', '.join(['%s:%s' % (repr(k), v) for k, v in vec if not k.startswith('_')])
      default:
        #say '@@3', 'default', type(a), a
        raise 'ToJson: Strange Value', type(a), a

###############################
# Regular Expression Functions
Special = regexp.MustCompile('^[][{}()=]$').FindString
ReplaceSpecialsAnywhere = regexp.MustCompile('([][{}();])').ReplaceAllString
ReplaceComment = regexp.MustCompile('[#].*').ReplaceAllString

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
#   -- Add spaces arund Specials ( ) [ ] { } ;
#   -- split lines on white space.
#   -- Add ';' to end of every line.
#   -- Return list of token tuples (value, lineno).
class Lex:
  def __init__(program):
    .program = ReplaceSpecialsAnywhere(program, ' $1 ')
    #say .program
    .toks = .lexProgram()

  def lexLine(line):
    #say line
    line = ReplaceComment(line, '')
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
#  -- Bare:  a bare word, like x
#  -- Dollar: a word starting with Dollar, like $x
#  -- Command: a parenthesized nonempty list of words, like (+ $x 1)
#  -- Tuple: a Named Tuple, like { a = foo ; b = 99 }
#  -- Derive:  a Derived Tuple, like tmpl... in { ... ; x = tmpl { p = 80 } ; ... } 
#  -- Enhance  an Enhanced Derived Tuple, like stuff... in { ... ; x = tmpl { stuff { another = 443 }  } ; ... } 

class AST:
  def isBare():
    return False
  def isDollar():
    return False
  def isCommand():
    return False

class Derive(AST):  # Enhance a derived subtuple.
  def __init__(template, diff):
    .template = template
    .diff = diff
    .dic = {}
  def visit(w, **kw):
    return w.visitDerive(self, **kw)
  def find(k):
    if k in .dic:
      return .dic[k]
    else:
      raise 'Cannot find slot %q in Tuple %q' % (k, str(self))
  def __str__():
    return '(Derive(%q): %v)' % (.template, .diff)

class Enhance(AST):  # Derive from a tuple.
  def __init__(dslot, diff):
    .dslot = dslot
    .diff = diff
  def visit(w, **kw):
    return w.visitEnhance(self, **kw)
  def __str__():
    return '(Enhance(%q): %v)' % (.dslot, .diff)

class Tuple(AST): # Named tuple with {...}.
  def __init__(dic):
    .dic = dic
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

class Dollar(AST): # Dollar substituted bareword.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitDollar(self, **kw)
  def __str__():
    return '<$%v>' % .a
  def isDollar():
    return True

class Bare(AST):  # Bareword has its own value.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitBare(self, **kw)
  def __str__():
    return '<%v>' % .a
  def isBare():
    return True

class Command(AST):  # Parenthesized command.
  def __init__(vec):
    .vec = vec
  def visit(w, **kw):
    return w.visitCommand(self, **kw)
  def __str__():
    return '<( %v )>' % .vec
  def isCommand():
    return True

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
      if word.startswith('$'):
        z.append( Dollar(word[1:]) )
      elif word.startswith('('):
        .next()
        zzz = .command()
        #say zzz, .p[.i]
        z.append( zzz )
        continue  # Do not throw away the next token.
      else:
        must not Special(word), word
        z.append( Bare(word) )
      .next()
    #say '<<<', .p[.i:]
    .next()
    #say '>>>', .p[.i:]
    #say '>>>', z
    return Command(z)

  def tuple():
    d = {}
    while .p[.i][0] != '}':
      k, kl = .p[.i]
      .next()
      if k == ';':
        continue
      must not Special(k), k, .p[.i:]

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
    z = .expr2()
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
# Destination & Source visitors.

class DstVisitor:
  def __init__(src, dst):
    .src = src  # Source tree to be made.
    .dst = dst  # Destination tree to be made.

  def visitTuple(p, spath, dpath, desired, level, **kw):
    #say spath, dpath, kw, desired, level
    d = dict(__name__=dpath, __src__=spath)
    .dst[dpath] = d
    for k, v in sorted(p.dic.items()):
      #say spath, dpath, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      v.visit(self, spath=spath2, dpath=dpath2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

  def visitDerive(p, spath, dpath, desired, level, **kw):
    template = R(p.template, D(spath))
    #say spath, dpath, kw, template, desired, level
    d = dict(__name__=dpath, __src__=spath, __template__=p.template)
    .dst[dpath] = d
    level += 1
    if level > desired:
      return

    # TODO -- allow Derive & Enhance, as well as Tuple, as template.
    tp = .src.get(template)
    #say tp, template

    if type(tp) is tuple:
      spath8, dpath8 = tp
      tp2 = .src.get(spath8)
      #say tp, tp2, spath8, dpath8
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
      #say spath, dpath, template, kw, k, v, desired, level
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
      #say spath, dpath, template, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      sup2 = J(template, k)
      v.visit(self, spath=spath2, dpath=dpath2, sup=sup2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

  def visitEnhance(p, spath, dpath, sup, desired, level, **kw):
    #say spath, dpath, kw, desired, level
    d = dict(__name__=dpath, __src__=spath, __slot__=p.dslot)
    .dst[dpath] = d
    level += 1
    if level > desired:
      return

    #say spath, dpath, kw, sup, desired, level

    td = .dst.get(sup)  # TODO
    if td:
      must type(td) == dict
      for k, v in sorted(td.items()):
        #say spath, dpath, kw, sup, td, k, v, desired, level
        spath2 = J(spath, k)
        dpath2 = J(dpath, k)
        # TODO
        # v.visit(self, spath=spath2, dpath=dpath2)
        d[k] = (spath2, dpath2)

    # Then the diffs.
    for k, v in sorted(p.diff.dic.items()):
      #say spath, dpath, kw, k, v, desired, level
      spath2 = J(spath, k)
      dpath2 = J(dpath, k)
      v.visit(self, spath=spath2, dpath=dpath2, desired=desired, level=level)
      d[k] = (spath2, dpath2)

  def visitBare(p, spath, dpath, desired, level, **kw):
    #say spath, dpath, kw, desired, level
    .dst[dpath] = p

  def visitDollar(p, spath, dpath, desired, level, **kw):
    #say spath, dpath, kw, desired, level
    .dst[dpath] = p

  def visitCommand(p, spath, dpath, desired, level, **kw):
    #say spath, dpath, kw, desired, level
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
    #say '@@@', z, path
    return z

  def visitDerive(p, path, **kw):
    z = 1
    Make(.src, path)
    for k, v in sorted(p.diff.dic.items()):
      path2 = J(path, k)
      Set(v, .src, path2)
      z = max(z, z + v.visit(self, path=path2))
    #say '@@@', z, path
    return z

  def visitEnhance(p, path, **kw):
    z = 1
    Make(.src, path)
    for k, v in sorted(p.diff.dic.items()):
      # p.dslot ?
      path2 = J(path, k)
      Set(v, .src, path2)
      z = max(z, z + v.visit(self, path=path2))
    #say '@@@', z, path
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

def main(argv):
  s = '{ %s }' % ioutil.ReadFile('/dev/stdin')
  c = Compile(s)
  if len(argv) == 0:
    print c.ToJson()
  else:
    for a in argv:
      print '# %s', a
      print c.ToJson(a)

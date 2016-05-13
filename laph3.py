from go import path as P, io/ioutil, os, regexp, strconv
from rye_lib import data
from . import chucl3, util
from . import laph3x as X


###############################
# Path Manipulation
B = P.Base
C = P.Clean
D = P.Dir
def J(*args): # Join
  return C(P.Join(*args))
def H(path): # Head
  """Head of path (the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return vec[0] if vec else ''
def T(path): # Tail
  """Tail of path (all but the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return J(*vec[1:]) if len(vec) > 1 else ''
def HT(path): # Head & Tail
  return H(path), T(path)
def S(path):  # Split
  return [e for e in path.split('/') if e]

###############################
# Lexical Analysis:
#   -- Add spaces arund Specials ( ) [ ] { } ;
#   -- split lines on white space.
#   -- Add ';' to end of every line.
#   -- Return list of token tuples (value, lineno).

Special = regexp.MustCompile('^[][{}()=]$').FindString
ReplaceSpecialsAnywhere = regexp.MustCompile('([][{}();])').ReplaceAllString
ReplaceComment = regexp.MustCompile('[#].*').ReplaceAllString

class Lex:
  def __init__(program):
    .program = ReplaceSpecialsAnywhere(program, ' $1 ')
    .toks = .lexProgram()

  def lexLine(line):
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
#  -- Command: a parenthesized nonempty list of words, like (+ $x 1)
#  -- Tuple: a Named Tuple, like { a = foo ; b = 99 }
#  -- Derive:  a Derived Tuple, like tmpl... in { ... ; x = tmpl { p = 80 } ; ... }
#  -- Enhance  an Enhanced Derived Tuple, like stuff... in { ... ; x = tmpl { stuff { another = 443 }  } ; ... }

class AST:
  def __repr__():
    return .__str__()
  def simplify():
    raise 'Cannot simplify a %T' % self

class Derive(AST):  # Derive from a tuple.
  def __init__(template, diff):
    .template = template
    .diff = diff
  def visit(w, **kw):
    say 'visiting...<<<', kw, self
    z = w.visitDerive(self, **kw)
    say 'visited', kw, '>>>', z
    return z
  def __str__():
    return '(Derive(%q): %v)' % (.template, .diff)

class Enhance(AST):  # Enhance a derived tuple.
  def __init__(dslot, diff):
    .dslot = dslot
    .diff = diff
  def visit(w, **kw):
    say 'visiting...<<<', kw, self
    z = w.visitEnhance(self, **kw)
    say 'visited', kw, '>>>', z
    return z
  def __str__():
    return '(Enhance(%q): %v)' % (.dslot, .diff)

class Tuple(AST): # Named tuple with {...}.
  def __init__(dic):
    .dic = dic
  def visit(w, **kw):
    say 'visiting...<<<', kw, self
    z = w.visitTuple(self, **kw)
    say 'visited', kw, '>>>', z
    return z
  def __str__():
    return '{Tuple: %s }' % (' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))

class Bare(AST):  # Bareword has its own value.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitBare(self, **kw)
  def __str__():
    return '< %v >' % .a
  def simplify():
    return str(.a)

class Command(AST):  # Parenthesized command.
  def __init__(cmdvec):
    .cmdvec = cmdvec
  def visit(w, **kw):
    return w.visitCommand(self, **kw)
  def __str__():
    return '<( %v )>' % .cmdvec
  def simplify():
    return tuple([x.simplify() for x in .cmdvec])

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

  def ParseCommand():
    z = []
    while .p[.i][0] != ')':
      word, wordl = .p[.i]
      if word.startswith('('):
        .next()
        zzz = .ParseCommand()
        z.append( zzz )
        continue  # Do not throw away the next token.
      else:
        must not Special(word), word
        z.append( Bare(word) )
      .next()
    .next()
    return Command(z)

  def ParseTuple():
    z = .ParseTupleGuts()
    token = .p[.i][0] if .i < len(.p) else '*EOF*'
    if token != '}':
      raise 'At end of tuple, expected "}" but got %q' % token
    .next()
    return z

  def ParseTupleGuts():
    d = {}
    while True:
      if len(.p) <= .i:
        break
      if .p[.i][0] == '}':
        break
      k, kl = .p[.i]
      .next()
      if k == ';':
        continue
      must not Special(k), k, .p[.i:]
      must not '/' in k

      op, ol = .p[.i]
      must Special(op), k, op, kl, ol
      switch op:
        case '=':
          .next()
          val = .ParseExpr()
          d[k] = val
        case '{':
          tup = .ParseExpr()
          must type(tup) is Tuple
          d[k] = Enhance(k, tup.dic)  # TODO
    # end while
    return Tuple(d)

  def ParseExpr():
    .d += 1
    z = .parseExpr2()
    .d -= 1
    return z

  def parseExpr2():
    x, xl = .p[.i]
    .next()
    if Special(x):
      switch x:
        case '(':
          return .ParseCommand()
        case '{':
          return .ParseTuple()
        default:
          raise str(('Default', x, .i, .p[.i]))

    else: # if not Special
      peek, peekl = .p[.i]
      if peek == ';' or peek == '}':
        return Bare(x)
      elif peek == '{':
        tup = .ParseExpr()
        must type(tup) is Tuple
        return Derive(x, tup.dic)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]

class ExpandingVisitor:
  def __init__():
    .dd = DeepDict()

  def visitTuple(p, path='/'):
    if .get(path) is None: .put(path, {})
    for k, v in p.dic.items():
      if k.startswith('__'): raise 'Cannot handle __ names', k
      if k.startswith('__'): continue
      say v, J(path, k)
      v.visit(self, path=J(path, k))

  def visitDerive(p, path):
    # template, diff
    if .get(path) is None: .put(path, {})
    .put(path, {})
    h, t = HT(p.template)
    d = D(path)
    while True:
      if .exists(J(d, h)):
        break
      d = D(path)
      if d in ('', '/', '.'):
        break

    src = J(d, p.template)
    if not .exists(src):
      say 'NOT YET', path, p.template, d, src
      return

    .copy(src, path)
    for k, v in p.diff.items():
      if k.startswith('__'): continue
      v.visit(self, path=J(path, k))

  def visitEnhance(p, path):
    # dslot, diff
    for k, v in p.diff.items():
      if k.startswith('__'): continue
      v.visit(self, path=J(path, k))

  def visitBare(p, path):
    .put(path, str(p.a))
    return p.a

  def visitCommand(p, path):
    .put(path, p.simplify())

  def put(path, value):
    steps = [e for e in path.split('/') if e]
    .dd.put(steps, value)

  def get(path):
    steps = [e for e in path.split('/') if e]
    return .dd.get(steps)

  def exists(path):
    x = .get(path)
    return x is not None

  def copy(path_from, dest):
    def traverse(s, d):
      if d:
        for k, v in d.items():
          if k.startswith('__'): continue
          s2 = J(s, k) if s else k
          if type(v) is dict:
            traverse(s2, v)
          else:
            .put(J(dest, s2), v)
    if .get(dest) is None: .put(dest, {})
    traverse('', .get(path_from))

class DeepDict:
  def __init__():
    .guts = {}

  """Get the value stored down sequence of keys.  If any subkey does not exist, return None."""
  def get(keys):
    if not keys: return .guts
    steps, last = keys[:-1], keys[-1]
    d = .guts
    for e in steps:
      d = d.get(e)
      if d is None:
        return None
    return d.get(last)

  """Put the value sequence of keys.  If any subkey does not exist, create subdictionaries."""
  def put(keys, value):
    if not keys: return
    steps, last = keys[:-1], keys[-1]
    d = .guts
    for e in steps:
      if e in d:
        d = d[e]
      else:
        t = {}
        d[e] = t
        d = t
    d[last] = value

  def items(hidden=False):
    z = []
    def traverse(steps, d):
      for k, v in d.items():
        if k.startswith('_') and not hidden:
          continue
        if type(v) is dict:
          traverse(steps + [k], v)
        else:
          z.append((steps + [k], v))
    traverse([], .guts)
    return sorted(z)


class Compile:
  def __init__(program):
    .program = program
    parsed = Parse(program)  # Creates the parser.
    .tree = parsed.ParseTupleGuts()  # Actually parses, as if the guts of a tuple.
    must type(.tree) == Tuple, 'Expected program to be a Tuple, but got %q' % type(.tree)

    .expanded = ExpandingVisitor()
    was = 0
    while True:
      .expanded.visitTuple(.tree)
      items = .expanded.dd.items(True)
      n = len(items)
      say was, n
      if n == was: break
      was = n
    .chucl = chucl3.Chucl(.expanded.dd.guts)

    say .expanded.dd.guts
    util.PrettyPrint(.expanded.dd.guts)

    for k, v in items:
      say k, v, type(k), type(v)
      if (type(v) is tuple and v[0] != 'error') or type(v) is str and v.startswith('$'):
        try:
          path = J('/', *k)
          x = .Eval(path)
        except as err:
          x = ('error', str(err))
        say k, v, path, x
        .expanded.dd.put(k, x)

  def Eval(path):
    return .chucl.Eval(path)

class CompileX:
  def __init__(program):
    .program = program
    parsed = Parse(program)  # Creates the parser.
    .tree = parsed.ParseTupleGuts()  # Actually parses, as if the guts of a tuple.
    must type(.tree) == Tuple, 'Expected program to be a Tuple, but got %q' % type(.tree)

    .r = {}
    .i = 1
    .tree.visit(self, path='/', up=0)

  def visitTuple(p, path, up):
    i = .i
    .i += 1
    .r[i] = {}
    if up:
      .r[up][B(path)] = i
    for k, v in p.dic.items():
      v.visit(self, path=J(path, k), up=i)

  def visitDerive(p, path, up):
    i = .i
    .i += 1
    .r[i] = {}
    if up:
      .r[up][B(path)] = i
    for k, v in p.diff.items():
      v.visit(self, path=J(path, k), up=i)
    .r[i]['__base'] = p.template

  def visitEnhance(p, path, up):
    i = .i
    .i += 1
    .r[i] = {}
    if up:
      .r[up][B(path)] = i
    for k, v in p.diff.items():
      v.visit(self, path=J(path, k), up=i)
    .r[i]['__enhance'] = p.dslot

  def visitBare(p, path, up):
    .r[up][B(path)] = p.a

  def visitCommand(p, path, up):
    .r[up][B(path)] = p.cmdvec

  def Resolve(path):
    return X.Resolve(.r, path)

  def PrintAll():
    def walk(i, path):
      for k, v in sorted(.r[i].items()):
        path_ = J(path, k)
        if type(v) is int:
          walk(v, path_)
        else:
          print path_, v
          print path_, v
    walk(1, '/')

  def PrintAllResolved():
    def walk(path):
      stuff = X.Resolve(.r, path)
      if type(stuff) is set:
        for e in sorted(stuff):
          walk(J(path, e))
      else:
        print path, stuff
    walk('/')

def Old_main(argv):
  s = ioutil.ReadFile('/dev/stdin')
  c = Compile(s)
  say c.expanded.dd.guts
  i = 0
  for k, v in c.expanded.dd.items(hidden=False):
    i += 1
    print i, k, '=======', v
    if type(v) is tuple:
      try:
        #print '>>>>>>', c.chucl.Eval(J(*k))
        print '>>>>>>', c.Eval(J(*k))
      except as ex:
        print '>>>>>>!!!!!!', ex

def main(argv):
  s = ioutil.ReadFile('/dev/stdin')
  c = CompileX(s)
  util.PrettyPrint(c.r)
  print '#################################'
  c.PrintAll()
  print '#################################'
  c.PrintAllResolved()

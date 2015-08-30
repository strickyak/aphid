from go import path as P, regexp, io/ioutil, strconv
from . import laph7_chucl as laph_chucl

MAX_DELEGATION = 4  # Awful hack.  Should get feedback, if things fail.

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

class Derive(AST):  # Derive from a tuple.
  def __init__(template, diff):
    .template = template
    .diff = diff
  def visit(w, **kw):
    say 'visiting...', kw, self
    z = w.visitDerive(self, **kw)
    say 'visited', kw, '>>>', z
    return z
  def __str__():
    return '(Derive(%q): %v)' % (.template, .diff)
  def __repr__(): return .__str__()

class Enhance(AST):  # Enhance a derived tuple.
  def __init__(dslot, diff):
    .dslot = dslot
    .diff = diff
  def visit(w, **kw):
    say 'visiting...', kw, self
    z = w.visitEnhance(self, **kw)
    say 'visited', kw, '>>>', z
    return z
  def __str__():
    return '(Enhance(%q): %v)' % (.dslot, .diff)
  def __repr__(): return .__str__()

class Tuple(AST): # Named tuple with {...}.
  def __init__(dic):
    .dic = dic
  def visit(w, **kw):
    return w.visitTuple(self, **kw)
  def __str__():
    return '{Tuple: %s }' % (' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))
  def __repr__(): return .__str__()

class Dollar(AST): # Dollar substituted bareword.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitDollar(self, **kw)
  def __str__():
    return '<$%v>' % .a
  def __repr__(): return .__str__()
  def isDollar():
    return True

class Bare(AST):  # Bareword has its own value.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitBare(self, **kw)
  def __str__():
    return '<%v>' % .a
  def __repr__(): return .__str__()
  def isBare():
    return True

class Command(AST):  # Parenthesized command.
  def __init__(cmdvec):
    .cmdvec = cmdvec
  def visit(w, **kw):
    return w.visitCommand(self, **kw)
  def __str__():
    return '<( %v )>' % .cmdvec
  def __repr__(): return .__str__()
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

  def ParseCommand():
    z = []
    while .p[.i][0] != ')':
      word, wordl = .p[.i]
      if word.startswith('$'):
        z.append( LeafNode(Dollar(word[1:])) )
      elif word.startswith('('):
        .next()
        zzz = .ParseCommand()
        z.append( LeafNode(zzz) )
        continue  # Do not throw away the next token.
      else:
        must not Special(word), word
        z.append( LeafNode(Bare(word)) )
      .next()
    .next()
    return Command(z)

  def ParseTuple():
    z = .ParseTupleGuts()
    if .p[.i][0] != '}':
      raise 'At end of tuple, expected "}" but got %q' % .p[.i][0]
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
    #start = .p[.i:]
    z = .parseExpr2()
    #say start, '>>>', z
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
        if x.startswith('$'):
          return Dollar(x[1:])
        else:
          return Bare(x)
      elif peek == '{':
        tup = .ParseExpr()
        must type(tup) is Tuple
        return Derive(x, tup.dic)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]

MATCH_INTEGER = regexp.MustCompile('^-?[0-9]+$').FindString

class Compile22:
  def __init__(program):
    .program = program
    say .program
    parsed = Parse(program)
    say parsed.p
    .tree = parsed.ParseTupleGuts()
    say .tree
    must type(.tree) == Tuple, 'Expected program to be a Tuple, but got %q' % type(.tree)

    #.look = {}

    def lookup_fn(k):
      return .visitor.visitTuple(.tree, path=k, up='/')

    def command_ctor(a):
      return LeafNode(Command(a))

    def value_ctor(a):
      return LeafNode(Bare(a))

    .chucl = laph_chucl.Evaluator(lookup_fn, command_ctor, value_ctor)
    .visitor = EvalVisitor33(self)

  def Eval(path):
    path = C(path)
    say '#'
    say '<<<<<<<<<', path
    z = .chucl.EvalPath(path)
    say '>>>>>>>>>', path, z
    say '#'
    return z

  def Keys(path):  # that are not _hidden.
    path = C(path)
    d = .chucl.EvalPath(path)
    return sorted([k for k in d if not k.startswith('_')])

  def ToListing(path='/'):
    path = C(path)
    a = .Eval(path)
    switch type(a):
      case "*rye.PNone":
        print "%s == **None**" % path
      case LeafNode:
        print "%s == %s" % (path, a.leaf)
      case DirNode:
        #print "%s :: [[[ %s ]]]" % (path, a.names)
        for name in a.names:
          .ToListing(J(path, name))


  def ToJson(path='/'):
    path = C(path)
    a = .Eval(path)
    switch type(a):
      case int:
        return repr(a)
      case float:
        return repr(a)
      case str:
        if MATCH_INTEGER(a):
          return a
        return repr(a)
      case list:
        vec = [.ToJson(J(path, e)) for e in a]
        return '[%s]' % ','.join(vec)
      case dict:
        vec = [(k, .ToJson(J(path, k))) for k, v in sorted(a.items()) if not k.startswith('_')]
        return '{%s}' % ', '.join(['%s:%s' % (repr(k), v) for k, v in vec if not k.startswith('_')])
      default:
        raise 'ToJson: Strange Value', type(a), a

class Node:
  def IsNode():
    return True

class LeafNode(Node):
  def __init__(leaf):
    .leaf = leaf
  def IsLeaf():
    return True
  def IsDir():
    return False
  def __str__():
    return 'L(%s)' % .leaf
  def __repr__():
    return 'L(%s)' % .leaf

class DirNode(Node):
  def __init__(names):
    .names = names
  def IsLeaf():
    return False
  def IsDir():
    return True
  def __str__():
    return 'D{%s}' % ','.join(.names)
  def __repr__():
    return 'D{%s}' % ','.join(.names)

class EvalVisitor33:
  """Evaluate a path."""
  def __init__(compiler):
    #.look = compiler.look  # Lookup table of Source AST objects.
    .chucl = compiler.chucl  # The Command Interpreter.

  def visitTuple(p, path, up, **kw):
    h, t = HT(path)
    say up, h, t
    if h:
      if h in p.dic:
        # Continue with next key.
        return p.dic[h].visit(self, path=t, up=J(up, h), **kw)
      else:
        # Error: key not found :-> None.
        return None
    else:
      # Path ends here -- we are the DirNode.
      return DirNode(sorted(p.dic.keys()))

  def visitDerive(p, path, up, **kw):
    h, t = HT(path)

    must type(p.template) is str
    say p.template, h, t, up, D(up)
    base = .chucl.EvalPath(J(p.template, h, t), D(up))
    say p.template, J(p.template, h, t), base

    if h:
      if h in p.diff:
        dif = p.diff[h].visit(self, path=t, up=J(up, h), **kw)

      if dif is not None and dif.IsLeaf():
        # A single value was found in the diff.
        return dif
      # dif is not LeafNode.

      if dif is None and base is not None and base.IsLeaf():
        return base
      if base is not None and base.IsLeaf():
        raise 'Conflict: base is Leaf, but dif is Dir: %q/%q/%q' % (up, h, t)

      # Override base with elements of dif.
      say base
      z = {}
      for e in sorted(base.names if base else []):
        z[e] = True
      return DirNode(sorted(z.keys()))

    # Override dic with elements of diff.
    must base is None or base.IsDir()
    z = dict([(e, True) for e in (base.names if base else [])])
    for k, _ in sorted(p.diff.items()):
      z[k] = True
    return DirNode(sorted(z.keys()))


  def visitEnhance(p, path, up, **kw):
    h, t = HT(path)
    if h:
      if h in p.diff:
        dif = p.diff[h].visit(self, path=t, up=J(up, h), **kw)

      if dif is None or dif.IsLeaf():
        return dif

      return DirNode(sorted(p.diff.keys()))

  def visitBare(p, path, **kw):
    return LeafNode(p)

  def visitDollar(p, path, **kw):
    return LeafNode(p)
    #return LeafNode('{{{Dollar:%s}}}' % p.a)

  def visitCommand(p, path, **kw):
    return LeafNode(p)
    #return LeafNode('{{{Command:%s}}}' % str(p.cmdvec))

def main(argv):
  s = ioutil.ReadFile('/dev/stdin')
  c = Compile22(s)

  if len(argv) == 0:
    print c.ToListing()
  else:
    for a in argv:
      print '# %s' % a
      #print c.ToJson(a)
      c.ToListing(a)

pass

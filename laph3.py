from go import bytes, path as P, io/ioutil, os, regexp, strconv
from rye_lib import data
from . import chucl3x, util

NONE = ()

###############################
# Path Manipulation
B = P.Base
C = P.Clean
D = P.Dir
def J(*args): # Join
  return C(P.Join(*args))
def S(path):  # Split
  return [e for e in path.split('/') if e]
def H(path): # Head
  """Head of path (the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return vec[0] if vec else ''
def T(path): # Tail
  """Tail of path (all but the first name) or Empty."""
  vec = [e for e in path.split('/') if e]
  return J(*vec[1:]) if len(vec) > 1 else ''
def HT(path): # Head & Tail
  vec = [e for e in path.split('/') if e]
  h = vec[0] if vec else ''
  t = J(*vec[1:]) if len(vec) > 1 else ''
  return h, t

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
      elif word.startswith('$') and len(word) > 1:
        z.append( Command([ Bare('get'), Bare(word[1:]) ]) )
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
        if x.startswith('$') and len(x) > 1:
          return Command([ Bare('get'), Bare(x[1:]) ])
        else:
          return Bare(x)
      elif peek == '{':
        tup = .ParseExpr()
        must type(tup) is Tuple
        return Derive(x, tup.dic)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]

class Compile:
  def __init__(program):
    .program = program
    parsed = Parse(program)  # Creates the parser.
    .tree = parsed.ParseTupleGuts()  # Actually parses, as if the guts of a tuple.
    must type(.tree) == Tuple, 'Expected program to be a Tuple, but got %q' % type(.tree)

    .root = {}
    .i = 1
    .tree.visit(self, path='/', up=0)
    .chucl = chucl3x.Chucl(self)

    .resolve_cache = {}

  def visitTuple(p, path, up):
    i = .i
    .i += 1
    .root[i] = {}
    if up:
      .root[up][B(path)] = i
    for k, v in p.dic.items():
      v.visit(self, path=J(path, k), up=i)

  def visitDerive(p, path, up):
    i = .i
    .i += 1
    .root[i] = {}
    if up:
      .root[up][B(path)] = i
    for k, v in p.diff.items():
      v.visit(self, path=J(path, k), up=i)
    .root[i]['____base'] = p.template

  def visitEnhance(p, path, up):
    i = .i
    .i += 1
    .root[i] = {}
    if up:
      .root[up][B(path)] = i
    for k, v in p.diff.items():
      v.visit(self, path=J(path, k), up=i)
    .root[i]['____enhance'] = p.dslot

  def visitBare(p, path, up):
    .root[up][B(path)] = p.a  # sets a str.

  def visitCommand(p, path, up):
    .root[up][B(path)] = p.cmdvec  # sets a list.

  def PrintAll():
    def walk(i, path):
      for k, v in sorted(.root[i].items()):
        path_ = J(path, k)
        if type(v) is int:
          walk(v, path_)
        else:
          print path_, v
          print path_, v
    walk(1, '/')

  def PrintAllResolved():
    def walk(path):
      stuff = .Resolve(path)
      if type(stuff) is set:
        for e in sorted(stuff):
          walk(J(path, e))
      else:
        print path, stuff
    walk('/')

  def PrintAllEvaluated():
    def walk(path):
      stuff = .chucl.EvalPath(path)
      if type(stuff) is set:
        for e in sorted(stuff):
          walk(J(path, e))
      else:
        print path, stuff
    walk('/')

  def ToJson(path='/', hidden=False):
    w = go_new(bytes.Buffer)
    def traverse(a, pre):
      if type(a) is dict:
        print >>w, '%s{' % pre
        for k, v in sorted(a.items()):
          if hidden or not k.startswith('_'):
            print >>w, '%s  %q :' % (pre, k)
            traverse(v, pre+'    ')
        print >>w, '%s}%s' % (pre, ',' if pre else '')
      else:
        print >>w, '%s%s,' % (pre, repr(a))

    x = .chucl.EvalPath(path)
    traverse(x, '')
    return str(w)

  def EvalPath(path):
    say '<<<', path
    stuff = .chucl.EvalPath(path)
    say '>>>', path, stuff
    return stuff

  def ToData(path='/'):
    return .EvalPath(path)

  def AbsolutePathRelativeTo(path, dir):
    # Handle case of absoulte path.
    if path.startswith('/'):
      return path

    # Search dir and its superdirs for the head of the relative path.
    hd, tl = HT(path)
    if not hd:
      return dir

    dir = '/%s' % dir
    while True:
      try:
        x = .Resolve(J(dir, hd))
        # If that does not throw an exception or return None
        if x is not None:
          return J(dir, path)
      except:
        pass  # Continue to try with superdir.
      if dir=='/':
        raise 'Cannot find path %q relative to directory %q' % (path, dir)
      dir = D(dir)
    raise 'NOTREACHED'

  def Keys(path : str) -> set:
    r = .Resolve(path)
    must type(r) is set
    return r

  def Resolve(path):
    z = .resolve_cache.get(path, NONE)
    if z is not NONE: return z

    z = .Resolve9(path)
    say 'RESOLVED', path, z
    .resolve_cache[path] = z
    return z

  def Resolve9(path):
    words = [e for e in path.split('/') if e and e != '.']
    context = [ 1 ]
    envs = []
    say 'RESOLVE', path, words

    z = None
    sofar = '/'
    for w in words + [None]:
      say 'RESOLVE WORD', w, context

      # Return for terminals.
      if w is None and z is not None:
        say path, z
        return z

      if z is not None:
        raise 'Got result %q before path %q is finished, at level %q' % (z, path, w)

      # Build the env for this level.
      env = dict()
      env['____path'] = sofar

      # For each input context, we append 5tuples for all vars to the env.
      for c in context:
        d = .root[c]
        say c, d

        def appendNormalKeyValuesToEnv(d_):
          for k, v in d_.items():
            if k.startswith('____'): continue
            if k not in env: env[k] = []
            say (context, c, d_, k, v)
            env[k].append( (context, c, d_, k, v) )
          pass

        appendNormalKeyValuesToEnv(d)
        #?baseContexts = []
        def followBases(child):
          # We may have a chain of ____base to merge in.
          base = child.get('____base')
          if not base:
            return

          say child, base
          must type(base) is str
          bb = [e for e in base.split('/') if e]
          must bb
          must len(bb) == 1  # We don't handle long bases yet.
          b0 = bb[0]

          # b0 is the name we are looking for, and found_b0 is a list of those we found.
          # Once we find at least one b0 at a level, we don't go up farther.
          found_b0 = []
          for up in Reversed(envs):
            say b0, up
            for got_b0 in up.get(b0):
              say b0, up, got_b0
              cx_, c_, d_, k_, v_ = got_b0
              say cx_, c_, d_, k_, v_
              if type(v_) is int:  # Int is a link to another Tuple.
                found_b0.append(v_)
            say b0, got_b0, found_b0
            if found_b0:
              break
          say b0, found_b0
          if not found_b0:
            raise 'Cannot find base key %q in context %s' % (base, str(c))
          for child_num_ in found_b0:
            child_ = .root[child_num_]
            appendNormalKeyValuesToEnv(child_)
            followBases(child_)
          #?baseContexts += found_b0
        followBases(d)

      envs.append(env)
      say 'BEFORE LEVEL %q OF %q' % (str(w), path)
      #util.PrettyPrint(env)

      # Return for tuple results.
      if w is None:
        z = set([e for e in env.keys() if not e.startswith('____')])
        say path, z
        return z

      # Build the context for the next level.
      nextContext = []
      answers = env.get(w)  # Get answer from env we built above.
      say w, answers, z
      if not answers:
        raise 'Key %q not found in context %s' % (w, repr(context))

      keys = []
      for (cx, c, d, k, v) in answers:
        say (cx, c, d, k, v)
        keys.append(k)
        say keys, type(v), v, z
        if type(v) is int:
          say v
          nextContext.append(v)
          say nextContext
        elif z is None:
          switch type(v):
            case str:
              z = v
            case list:
              def simplifyTerminalThing(thing):
                """Strip off the Bare and Command wrappers."""
                switch type(thing):
                  case Bare:
                    return thing.a
                  case Command:
                    return [simplifyTerminalThing(e) for e in thing.cmdvec]
                  case list:
                    return [simplifyTerminalThing(e) for e in thing]
                  default:
                    raise type(thing), repr(thing)
              z = simplifyTerminalThing(v)
            default:
              raise 'Weird type', type(v), v, (cx, c, d, k, v)
        else:
          pass # Because first terminal z sets z, and later ones are ignored.

      context = nextContext
      say context

      sofar = '%s/%s' % (sofar, w)

    raise 'NOTREACHED'

def Reversed(vec):
  z = [e for e in vec]
  z.reverse()
  return z

def main(args):
  s = ioutil.ReadFile('/dev/stdin')
  c = Compile(s)
  #util.PrettyPrint(c.root)
  #c.PrintAll()
  #c.PrintAllResolved()
  #print c.ToJson()
  for a in args:
    print '#>>>', a
    x = c.chucl.EvalPath(a)
    print data.PrettyPrint(x)

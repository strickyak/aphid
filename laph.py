from go import path as P, regexp, io/ioutil, strconv

MAX_DELEGATION = 4  # Awful hack.  Should get feedback, if things fail.

class Directory:
  def __init__(names):
    .names = names
  def __repr__():
    return 'D{%s}' % ','.join(.names)

###############################
# Path Manipulation
C = P.Clean
D = P.Dir
def J(*args):
  return C(P.Join(*args))
def Absolute(path, rel):
  """Resolve Relative or Absolute to Absoulte"""
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
  def isBare():
    return False
  def isCommand():
    return False

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
  def __repr__(): return .__str__()

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
  def __repr__(): return .__str__()

class Tuple(AST): # Named tuple with {...}.
  def __init__(dic):
    .dic = dic
  def visit(w, **kw):
    return w.visitTuple(self, **kw)
  def __str__():
    return '{Tuple: %s }' % (' ; '.join(['%v = %v' % (k, v) for k, v in sorted(.dic.items())]))
  def __repr__(): return .__str__()

class Bare(AST):  # Bareword has its own value.
  def __init__(a):
    .a = a
  def visit(w, **kw):
    return w.visitBare(self, **kw)
  def __str__():
    return '< %v >' % .a
  def __repr__(): return .__str__()
  def isBare():
    return True
  def simplify():
    return str(.a)

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
  def simplify():
    return [x.simplify() for x in .cmdvec]

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
        return Bare(x)
      elif peek == '{':
        tup = .ParseExpr()
        must type(tup) is Tuple
        return Derive(x, tup.dic)
      else:
        raise 'Bad Peek', .i, x, peek

    raise 'Unhandled', .i, .p[.i]

class Node:
  pass

class LeafNode(Node):
  def __init__(leaf):
    .leaf = leaf
  def IsLeaf():
    return True
  def IsDir():
    return False
  def __str__():
    return 'L{%s}' % .leaf
  def __repr__():
    return 'L{%s}' % .leaf
  def simplify():
    return .leaf.simplify()

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
  def simplify():
    return Directory(.names)

class EvalVisitor33:
  """Evaluate a path."""
  def __init__(compiler):
    .compiler = compiler

  def visitTuple(p, path, up, derived, **kw):
    h, t = HT(path)
    say up, h, t
    if h:
      if h in p.dic:
        # Continue with next key.
        return p.dic[h].visit(self, path=t, up=J(up, h), derived=J(derived, h), **kw)
      else:
        # Error: key not found :-> None.
        return None
    else:
      # Path ends here -- we are the DirNode.
      return DirNode(sorted(p.dic.keys()))

  def visitDerive(p, path, up, derived, **kw):
    say p, path, up, derived, kw
    h, t = HT(path)

    must type(p.template) is str
    say p.template, h, t, up, D(up)

    basepath = J(Absolute(p.template, D(up)))
    if h:
      if h in p.diff:
        say up, D(up), p.template, h, "DERIVED", J(basepath, h)
        dif = p.diff[h].visit(self, path=t, up=J(up, h), derived=J(basepath, h), **kw)

      if dif is not None and dif.IsLeaf():
        # A single value was found in the diff.
        return dif
      # dif is not LeafNode.

      base = .compiler.lookupNode(J(basepath, h, t))
      say p.template, J(p.template, h, t), base

      if dif is None and base is not None and base.IsLeaf():
        return base
      if base is not None and base.IsLeaf():
        raise 'Conflict: base is Leaf, but dif is Dir: %q/%q/%q' % (up, h, t)

      # Override base with elements of dif.
      say base, dif
      if not base and not dif:
        return None

      z = {}
      for e in base.names if base else []:
        z[e] = True
      for e in dif.names if dif else []:
        z[e] = True
      return DirNode(sorted(z.keys()))

    base = .compiler.lookupNode(J(basepath, h, t))
    say p.template, J(p.template, h, t), base

    # Override dic with elements of diff.
    must base is None or base.IsDir()
    z = dict([(e, True) for e in (base.names if base else [])])
    for k, _ in sorted(p.diff.items()):
      z[k] = True
    return DirNode(sorted(z.keys()))


  def visitEnhance(p, path, up, derived, **kw):
    must up != derived
    say p, path, up, derived, kw, self
    h, t = HT(path)
    say h, t
    if h:
      if h in p.diff:
        dif = p.diff[h].visit(self, path=t, up=J(up, h), derived=J(derived, h), **kw)
        say dif

      if dif is None or dif.IsLeaf():
        say dif
        return dif

      say p.diff, dif, h, t, up, derived
      return DirNode(sorted(dif.names))

    ## Override dic with elements of diff.
    base = .compiler.lookupNode(derived)
    must base is None or base.IsDir()
    z = dict([(e, True) for e in (base.names if base else [])])
    for k, _ in sorted(p.diff.items()):
      z[k] = True
    return DirNode(sorted(z.keys()))

  def visitBare(p, path, **kw):
    return LeafNode(p)

  def visitCommand(p, path, **kw):
    return LeafNode(p)

def main(argv):
  s = ioutil.ReadFile('/dev/stdin')
  c = Compile(s)

  if len(argv) == 0:
    print c.ToListing('/')
  else:
    for a in argv:
      print '# %s' % a
      print c.ToJson(a)

class Compile:
  def __init__(program):
    .program = program
    say .program
    parsed = Parse(program)
    say parsed.p
    .tree = parsed.ParseTupleGuts()
    say .tree
    must type(.tree) == Tuple, 'Expected program to be a Tuple, but got %q' % type(.tree)

    .chucl = Chucl(.Lookup)
    .visitor = EvalVisitor33(self)

  def Keys(path):
    return .Eval(path).names

  def Eval(path):
    return .chucl.EvalPath(C(path))

  def Lookup(path):
    node = .lookupNode(path)
    return None if node is None else node.simplify()

  def lookupNode(path):
    return .visitor.visitTuple(.tree, path=path, up='/', derived='/')

  def ToListing(path):
    path = C(path)
    try:
      a = .Eval(path)
    except as ex:
      a = 'EXCEPTION: ' + ex
    switch type(a):
      case type(None):
        print "%s == **None**" % path
      case str:
        print "%s == %s" % (path, a)
      case Directory:
        for name in a.names:
          .ToListing(J(path, name))

  def ToJson(path):
    path = C(path)
    a = .Eval(path)
    switch type(a):
      case type(None):
        return "null"
      case str:
        return "%q" % a
      case Directory:

        vec = [(k, .ToJson(J(path, k))) for k in sorted(a.names) if not k.startswith('_')]
        return '{%s}' % ', '.join(['%s:%s' % (repr(k), v) for k, v in vec if not k.startswith('_')])

    raise 'bad default %q' % str(type(a))

class Lambda:
  def __init__(formals, body):
    .formals = formals
    .body = body


class Chucl:
  def __init__(lookup_fn):
    .lookup_fn = lookup_fn

  def EvalPath(path, rel='/', binding=None):
    # Look in binding for the path (if it has no '/').
    if binding and not ('/' in path):
      if path in binding:
        return binding[path]

    # THIS IS THE UPLOOKING CODE.
    if path.startswith('/') or path.startswith('./') or path.startswith('../'):
      # Specific path was given; do not do up-looking.
      Qpath = Absolute(path, rel)
    else:
      # Search for the head name.
      h = H(path)
      d = rel
      while True:
        maybe = .lookup_fn(Absolute(h, d))
        if maybe: break
        if d == '.' or d == '' or d == '/': break
        d = D(d)
      if not maybe:
        say h, path
        raise 'Dollar: Cannot find %q from path %q starting at %q' % (h, path, rel)
      Qpath = Absolute(path, d)  # Rejoin d with entire path.

    # Now that you know how far up to go, lookup the final result.
    thing = .lookup_fn(Qpath)
    # And eval the result with Chucl.
    z = .EvalChucl(thing, Qpath, binding)
    return z

  def EvalChucl(thing, path, binding):
    if thing is None:
      return None

    Cpath = C(path)
    Dpath = D(Cpath)

    switch type(thing):
      case Directory:
        return thing

      case str:
        say '>>', thing, '>>leaf.isBare>>', thing

        if thing.startswith('$'):
          q = thing[1:]
          say '<<leaf.isDollar<<', q
          z = .EvalPath(q, Dpath, binding)
          say '>>', path, thing, q, Dpath, '>>leaf.isDollar>>', z
          must not z or type(z) is str
          return z
        else:
          return thing

      case list:
        say '->', thing, Cpath, '>>leaf.isCommand....'
        z = .EvalCommand(thing, Cpath, binding)
        say '>>', thing, Cpath, '>>leaf.isCommand>>', z
        return z

    raise 'EvalChucl cannot eval node of type %v' % type(thing)
  
  def EvalCommand(in_vec, Cpath, binding):
    vec = [(None if e is None else .EvalChucl(e, Cpath, binding)) for e in in_vec]

    cmd, args = vec[0], vec[1:]
    switch cmd:
      case '++':
        return ''.join(args)
      case '+':
        return str(sum([int(x) for x in args]))
      case '*':
        return str(reduce(lambda a, b: int(a)*int(b), args, 1))
      case 'lookup':
        must len(args) == 1
        return .EvalPath(args[0], rel=Cpath, binding=binding)
    raise 'EvalCommand: unknown cmd: %q' % cmd

#  def EvalCommand2(leaf, Cpath, binding):
#    raise 666
#    cmdvec = leaf.cmdvec
#    say cmdvec, Cpath, binding
#    must type(cmdvec) is list, cmdvec
#    must len(cmdvec), cmdvec
#    cmd = cmdvec[0].leaf
#
#    # Dereference if cmd is a Dollar.
#    if cmd.isBare() and cmd.a.startswith('$'):
#      cmd = .EvalPath(cmd.a[1:], D(Cpath), binding).leaf
#      say cmd
#
#    say cmd.isCommand(), type(cmd), cmd
#    # If cmd is lambda expression:
#    if cmd.isCommand():
#      #raise 'Lambdas not tested yet'
#      vec2 = cmd.cmdvec
#      must len(vec2) == 3, vec2
#      fn, formals, body = vec2
#      say type(fn), fn, type(formals), formals
#      must fn.leaf.isBare(), vec2
#      must fn.leaf.a == "fn", vec2
#      must formals.leaf.isCommand(), vec2  # Actually, a vec of formal parameters.
#      must len(formals.leaf.cmdvec) == len(cmdvec) - 1  # Correct number of args to formals.
#
#      binding2 = binding
#      for f, v in zip(formals.leaf.cmdvec, cmdvec[1:]):
#        raise 'binding2 = Binding(f.leaf.a, v, binding2)'
#        say f, v, binding2
#      z = .EvalNode(body, Cpath, binding2)
#      say vec2, z
#      return z
#
#    must cmd.isBare(), type(cmd), cmd
#    cmd = cmd.a
#    cmdvec = cmdvec[1:]
#
#    # Handle special forms.
#    switch cmd:
#      case 'lambda':
#        return leaf  # Lambda exprs eval to themselves.
#      case 'if':
#        must len(cmdvec) == 3, cmdvec
#        x, y, z = cmdvec
#        xv = .EvalNode(x, Cpath, binding)
#        s = xv.leaf.a if xv else None
#        if xv and xv!='False':
#          # True branch.
#          return .EvalNode(y, Cpath, binding)
#        else:
#          # False branch.
#          return .EvalNode(z, Cpath, binding)
#
#    # Handle other builtins.
#    args = []
#
#    say cmdvec
#    args = []
#    for a in cmdvec:
#      x = .EvalNode(a, Cpath, binding)
#      if x and x.IsDir():
#        say 'YAK GOT DirNode FROM EvalNode', a, Cpath, binding
#      args.append((x.leaf.a if x.leaf.isBare() else x.leaf.cmdvec) if x else None) 
#    say args
#
#    switch cmd:
#      case 'error':
#        raise 'ERROR(%s)' % str(args)
#
#    # Special code for the many binary operators.
#    if len(args) == 1:
#      x, = args
#      switch cmd:
#        case 'range':
#          return [str(e) for e in range(int(x))]
#        #case 'length':
#        #  z = str(len(Simple(x)))
#        #  return z
#        case 'error':
#          z = 'ERROR(%s)' % x
#
#    if len(args) == 2:
#      x, y = args
#      say x, y
#      switch cmd:
#        case '++':
#          return x + y
#        case '+':
#          return str(float(x) + float(y))
#        case '-':
#          return str(float(x) - float(y))
#        case '*':
#          return str(float(x) * float(y))
#        case '/':
#          return str(float(x) / float(y))
#        case '//':
#          return str(float(x) // float(y))
#        case '%':
#          return str(float(x) % float(y))
#        case '<':
#          return str(float(x) < float(y))
#        case '<=':
#          return str(float(x) <= float(y))
#        case '==':
#          return str(float(x) == float(y))
#        case '!=':
#          return str(float(x) != float(y))
#        case '>':
#          return str(float(x) > float(y))
#        case '>=':
#          return str(float(x) >= float(y))
#        case 'split':
#          return y.split(x)  # (split ch str)
#        case 'join':
#          return x.join(y)   # (join sep strs)
#
#        # String comparison
#        case 'lt':
#          return str(x < y)
#        case 'le':
#          return str(x <= y)
#        case 'eq':
#          return str(x == y)
#        case 'ne':
#          return str(x != y)
#        case 'gt':
#          return str(x > y)
#        case 'ge':
#          return str(x >= y)
#
#        case 'map':
#          return [.EvalCommand(.command_ctor([x, e]), Cpath, binding) for e in y]
#
#    # Fall through for other cases.
#    switch cmd:
#      case '++':
#        return ''.join([x for x in args])
#
#      case '+':
#        return str(sum([float(x) for x in args]))
#      case '*':
#        return reduce((lambda a,b: a*b), [float(x) for x in args])
#      case 'list':
#        return args
#
#    raise 'No such Chucl command: %q (or wrong number of args: %d)' % (cmd, len(args))

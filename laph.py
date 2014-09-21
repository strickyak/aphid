# from go import strings
from go import regexp
from go import os
from go import io/ioutil

PARENT = regexp.MustCompile('([A-Za-z0-9_.]+)[.]([A-Za-z0-9_]+)')

FRONT_WHITE = regexp.MustCompile('^(\\s+)')
FRONT_EQ = regexp.MustCompile('^[=]')
FRONT_WORDS = regexp.MustCompile('^(([A-Za-z_])([A-Za-z0-9_]*))([.](([A-Za-z_])([A-Za-z0-9_]*)))*')
FRONT_HEADER = regexp.MustCompile('^[[]\\s*((([A-Za-z])([A-Za-z0-9_]*))([.](([A-Za-z])([A-Za-z0-9_]*)))*)?\\s*[]]')
FRONT_OPEN = regexp.MustCompile('^[(]')
FRONT_CLOSE = regexp.MustCompile('^[)]')
FRONT_QUOTE = regexp.MustCompile("^[']")
FRONT_STRING = regexp.MustCompile('^"([^"]|"")*"')
FRONT_INT = regexp.MustCompile('^[-]?[0-9]+')
FRONT_FLOAT = regexp.MustCompile('^[-]?[0-9]+[.]?[0-9]+')  # No exponential notation.

L1 = [ ('Str', FRONT_STRING), ('Int', FRONT_INT), ('Float', FRONT_FLOAT) ]
L2 = [ ('Open', FRONT_OPEN), ('Close', FRONT_CLOSE), ('Quote', FRONT_QUOTE) ]
L3 = [ ('Eq', FRONT_EQ), ('Words', FRONT_WORDS), ('Header', FRONT_HEADER) ]
LEXERS = L1 + L2 + L3

assert FRONT_HEADER.FindString('[abc] xxx') == '[abc]'
assert FRONT_HEADER.FindString('[] xxx') == '[]'
assert not FRONT_WORDS.FindString(' FooBar.Baz')

QUOTE0 = regexp.MustCompile('^["]')
QUOTE1 = regexp.MustCompile('["]$')
QUOTE2 = regexp.MustCompile('["]["]')

Interned = {}

def Tokenize(text):
  z = []  # YAK
  while text:
    s = FRONT_WHITE.FindString(text)
    text = text[ len(s) : ]
    if text:
      for pair in LEXERS:
        pname, pattern = pair
        s = pattern.FindString(text)
        if s:
          # yield pname, s # YAK
          z.append(( pname, s )) # YAK
          text = text[ len(s) : ]
          break
      if not s:
        raise 'Cannot tokenize: ' + text
  return z # YAK

class Block:
  def __init__(engine):
    .name = None
    .up = None
    .slots = {}
    .engine = engine

  def Lookup(key):
    z = .slots.get(key)
    if z:
      return z
    elif .up:
      return .up.Lookup(key)
    else:
      return None

class Engine:
  def __init__(text):
    .blocks = {}
    .text = text
    .toks = list(Tokenize(text))
    .n = len(.toks)
    .p = -1
    .Advance()

  def Advance():
    if .p >= .n:
      .t = None
      .v = None
      return

    .p += 1
    if .p >= .n:
      .t = None
      .v = None
      return
    .t = .toks[.p][0]
    .v = .toks[.p][1]

  def MakeBlock(s):
    p = .blocks.get(s)
    if not p:
      p = Block(self)
      p.name = s
      .blocks[p.name] = p
      m = PARENT.FindStringSubmatch(s)
      if m:
        _, upname, _ = m
        p.up = .MakeBlock(upname)
      elif s != "":
        p.up = .MakeBlock("")
    return p

  def Parse():
    while .t:
      .ParseBlock()
    return self

  def ParseBlock():
    .MustT('Header')
    name = FRONT_HEADER.FindStringSubmatch(.v)[1]
    block = .MakeBlock(name)
    .Advance()

    while .t == 'Words':
      .ParseSlot(block)

  def ParseSlot(block):
    k = .v
    .Advance()

    .MustT('Eq')
    .Advance()

    v = .ParseExpr()
    block.slots[k] = v

  def ParseExpr():
    if not .t:
      raise "Expected expression but got End of String."
    if .t == 'Open':
      return .ParseList()
    if .t == 'Words':
      z = Intern(str(.v))
      .Advance()
      return z
    if .t == 'Int':
      z = Lit(int(.v))
      .Advance()
      return z
    if .t == 'Float':
      z = Lit(float(.v))
      .Advance()
      return z
    if .t == 'Str':
      s = .v
      s = QUOTE0.ReplaceAllString(s, '')
      s = QUOTE1.ReplaceAllString(s, '')
      s = QUOTE2.ReplaceAllString(s, '\"')
      z = Lit(str(s))
      .Advance()
      return z
    if .t == 'Quote':
      .Advance()
      x = .ParseExpr()
      return List([Intern('quote'), x])
    raise 'ParseExpr unknown: %s: %d' % (.t, .v)

  def ParseList():
    .MustT('Open')
    .Advance()
    z = []
    while .t != 'Close':
      x = .ParseExpr()
      z.append(x)
    .Advance()
    return List(z)

  def MustT(t):
    if .t != t:
      raise 'Expected %s, got %s: %s' % (t, .t, .v)

def Intern(s):
  assert type(s) == str
  sym = Interned.get(s)
  if sym is None:
    sym = Symbol(s)
    Interned[s] = sym
  return sym

_lambda = Intern("lambda")
_nil = Intern("nil")       # nil is False.
_true = Intern("true")
_false = Intern("false")       # false is False.

# Special fixed values:
_lambda.val = _lambda
_nil.val = List([])
_true.val = _true
_false.val = _false

class Node:
  def __init__():
    pass
  def Eq(a):
    return self is a

class Lit(Node):
  def __init__(x):
    .x = x
  def Eq(a):
    return .x == a.x if type(a) is Lit else False
  def Show():
    if type(.x) == str:
      return '"%s"' % .x  # TODO: fix for escaping.  TODO: why not just repr(.x)?
    else:
      return repr(.x)
  def Eval(env, block):
    return self
  def Bool():
    return True  # All Lits are True (unlike Python).

class Symbol(Node):
  def __init__(s):
    .s = s
    .prim = None  # If not None, it is a primative function.
    .val = None   # if not None, it has a predefined, fixed value.
  def Show():
    return .s
  def Lookup(env, block):
    if .val is not None:
      return .val
    for k, v in env:
      if .s == k:
        return v
    if block:
      return block.Lookup(.s)
  def Eval(env, block):
    return .Lookup(env, block)
  def Bool():
    return self is not _false

class List(Node):
  def __init__(v):
    .v = v

  def Eq(a):
    if len(.v) != len(a.v):
      return False
    for i in range(len(.v)):
      if not .v[i].Eq(a.v[i]):
        return False
    return True

  def Len():
    return len(.v)
  def Bool():
    return len(.v) != 0

  def Show():
    z = '('
    for x in .v:
      if len(z) > 1:
        z += ' '
      z += x.Show()
    return z + ')'

  def Eval(env, block):
    say 'List::Eval', self.Show(), env, (block.name if block else 'NO_STANZA')
    if len(.v) < 1:
      return self  # nil is self-evaluating.

    hd = .v[0]
    say hd, type(hd)
    if type(hd) is Symbol and hd.prim is not None:  # IF A PRIM:
      say hd.prim, self
      return hd.prim(self, env, block)

    cmd = hd.Eval(env, block)
    say cmd
    if type(cmd) is List:
      if len(cmd.v) == 3:
        lam, formals, expr = cmd.v
        if lam is _lambda and type(formals) is List:
          say formals, expr, .v
          if len(formals.v) == len(.v) - 1:
            env2 = env
            for i in range(len(formals.v)):
              assert type(formals.v[i]) is Symbol
              env2 = [(formals.v[i].s, .v[i+1].Eval(env, block))] + env2
            return expr.Eval(env2, block)
          else:
            raise 'Wrong number of formals (%s) vs args (%s)' % (len(formals.v), len(.v) - 1)

      raise 'Strange list in head position is not valid lambda expr: %s' % cmd.Show()
    raise 'Other: %s' % .Show()

def args(a, env, block):
  return [x.Eval(env, block) for x in a.v[1:]]

def arg2(a, env, block):
  assert len(a.v) == 3
  return args(a, env, block)

def dolambda(a, env, block):
  say 'dolambda', a
  return a  # Lambda exprs are self-evaluating.
_lambda.prim = dolambda

def doquote(a, env, block):
  must len(a.v) == 2
  return a.v[1]  # Quote returns first arg, unevaluated.
_quote = Intern('quote')
_quote.prim = doquote

def doif(a, env, block):
  must len(a.v) == 6
  s_if, cond, s_then, x, s_else, y = a.v
  must s_then is _then  # Required noise word 'then'
  must s_else is _else  # Required noise word 'else'
  cond = cond.Eval(env, block)
  if cond.Bool():
    return x.Eval(env, block)
  else:
    return y.Eval(env, block)
_if = Intern('if')
_if.prim = doif
_then = Intern('then')
_else = Intern('else')

def dolist(a, env, block):
  return args(a, env, block)
_list = Intern('list')
_list.prim = dolist

def dolt(a, env, block):
  b, c = arg2(a, env, block)
  return _true if ( b.x < c.x ) else _false
_lt = Intern('lt')
_lt.prim = dolt

def dole(a, env, block):
  b, c = arg2(a, env, block)
  return _true if ( b.x <= c.x ) else _false
_le = Intern('le')
_le.prim = dole

def doplus(a, env, block):
  b, c = arg2(a, env, block)
  return Lit( b.x + c.x )
_plus = Intern('plus')
_plus.prim = doplus

def dominus(a, env, block):
  b, c = arg2(a, env, block)
  return Lit( b.x - c.x )
_minus = Intern('minus')
_minus.prim = dominus

def dotimes(a, env, block):
  b, c = arg2(a, env, block)
  return Lit( b.x * c.x )
_times = Intern('times')
_times.prim = dotimes

def doexpect(a, env, block):
  b, c = arg2(a, env, block)
  must b.Eq(c), ';  LHS: %s  ;  RHS: %s' % (b.Show(), c.Show())
  return c
_expect = Intern('expect')
_expect.prim = doexpect

def main(argv):
  code = ioutil.ReadAll(os.Stdin)
  eng = Engine(code)
  eng.Parse()

  for name, st in sorted(eng.blocks.items()):
    must name == st.name
    print '[ %s ]' % name
    for k, v in sorted(st.slots.items()):
      print '  %s = %s' % (k, v.Eval([], st).Show())

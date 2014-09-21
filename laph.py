# from go import strings
from go import regexp
from go import os
from go import io/ioutil

PARENT = regexp.MustCompile('([A-Za-z0-9_.]+)[.]([A-Za-z0-9_]+)')

FRONT_WHITE = regexp.MustCompile('^(\\s+)')
FRONT_EQ = regexp.MustCompile('^[=]')
FRONT_WORDS = regexp.MustCompile('^(([A-Za-z_])([A-Za-z0-9_]*))([.](([A-Za-z_])([A-Za-z0-9_]*)))*')
FRONT_HEADER = regexp.MustCompile('^[[]\\s*((([A-Za-z])([A-Za-z0-9_]*))([.](([A-Za-z])([A-Za-z0-9_]*)))*)\\s*[]]')
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

class Stanza:
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
    .stanzas = {}
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

  def MakeStanza(s):
    sp = .stanzas.get(s)
    if not sp:
      sp = Stanza(self)
      sp.name = s
      .stanzas[sp.name] = sp
      m = PARENT.FindStringSubmatch(s)
      if m:
        _, upname, _ = m
        sp.up = .MakeStanza(upname)
    return sp

  def Parse():
    while .t:
      .ParseStanza()
    return self

  def ParseStanza():
    .MustT('Header')
    name = FRONT_HEADER.FindStringSubmatch(.v)[1]
    stanza = .MakeStanza(name)
    .Advance()

    while .t == 'Words':
      .ParseSlot(stanza)

  def ParseSlot(stanza):
    k = .v
    .Advance()

    .MustT('Eq')
    .Advance()

    v = .ParseExpr()
    stanza.slots[k] = v

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
Nil = Intern("nil")       # nil is False.
T = Intern("true")
F = Intern("false")       # false is False.

# Special fixed values:
_lambda.val = _lambda
Nil.val = List([])
T.val = T
F.val = F

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
  def Eval(env, stanza):
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
  def Lookup(env, stanza):
    if .val is not None:
      return .val
    for k, v in env:
      if .s == k:
        return v
    if stanza:
      return stanza.Lookup(.s)
  def Eval(env, stanza):
    return .Lookup(env, stanza)
  def Bool():
    return self != F

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

  def Eval(env, stanza):
    say 'List::Eval', self.Show(), env, (stanza.name if stanza else 'NO_STANZA')
    if len(.v) < 1:
      return self  # nil is self-evaluating.

    hd = .v[0]
    say hd, type(hd)
    if type(hd) is Symbol and hd.prim is not None:  # IF A PRIM:
      say hd.prim, self
      return hd.prim(self, env, stanza)

    cmd = hd.Eval(env, stanza)
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
              env2 = [(formals.v[i].s, .v[i+1].Eval(env, stanza))] + env2
            return expr.Eval(env2, stanza)
          else:
            raise 'Wrong number of formals (%s) vs args (%s)' % (len(formals.v), len(.v) - 1)

      raise 'Strange list in head position is not valid lambda expr: %s' % cmd.Show()
    raise 'Other: %s' % .Show()

def args(a, env, stanza):
  return [x.Eval(env, stanza) for x in a.v[1:]]

def arg2(a, env, stanza):
  assert len(a.v) == 3
  return args(a, env, stanza)

def dolambda(a, env, stanza):
  say 'dolambda', a
  return a  # Lambda exprs are self-evaluating.
_lambda.prim = dolambda

def doquote(a, env, stanza):
  assert len(a.v) == 2
  return a.v[1]  # Quote returns first arg, unevaluated.
_quote = Intern('quote')
_quote.prim = doquote

def dolist(a, env, stanza):
  return args(a, env, stanza)
_list = Intern('list')
_list.prim = dolist

def doplus(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x + c.x )
_plus = Intern('plus')
_plus.prim = doplus

def dominus(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x - c.x )
_minus = Intern('minus')
_minus.prim = dominus

def dotimes(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x * c.x )
_times = Intern('times')
_times.prim = dotimes

def main(argv):
  code = ioutil.ReadAll(os.Stdin)
  eng = Engine(code)
  eng.Parse()

  for name, st in sorted(eng.stanzas.items()):
    assert name == st.name
    print '[ %s ]' % name
    for k, v in sorted(st.slots.items()):
      print '  %s = %s' % (k, v.Eval([], st).Show())

from go import strings
from go import regexp

PARENT = regexp.MustCompile('([A-Za-z0-9_.]+)[.]([A-Za-z0-9_]+)')

FRONT_WHITE = regexp.MustCompile('^(\\s+)')
FRONT_EQ = regexp.MustCompile('^[=]')
FRONT_WORDS = regexp.MustCompile('^(([A-Za-z_])([A-Za-z0-9_]*))([.](([A-Za-z_])([A-Za-z0-9_]*)))*')
FRONT_HEADER = regexp.MustCompile('^[[]((([A-Za-z])([A-Za-z0-9_]*))([.](([A-Za-z])([A-Za-z0-9_]*)))*)[]]')
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

def Tokenize(text):
  while text:
    s = FRONT_WHITE.FindString(text)
    text = text[ len(s) : ]
    print 'TEXT', repr(text), 'WHITE WAS', repr(s)
    if text:
      for pair in LEXERS:
        pname, pattern = pair
        s = pattern.FindString(text)
        print 'TEXT', repr(text), 'PATTERN', pname, 'GOT', repr(s)
        if s:
          yield pname, s
          text = text[ len(s) : ]
          break
      if not s:
        raise 'Cannot tokenize: ' + text
  print 'Tokenize TERMINATING'

print 'Tokenize:', list(Tokenize(' [Lyric] we_re up=all.night2 == get_lucky '))

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
    else:
      if .slots.up:
        return .slots.up.Lookup(key)
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
      m = PARENT.FindStringSubmatch(s)
      .stanzas[sp.name] = sp
      if m:
        print 'm: ', m
        sp.up = .MakeStanza(m[1])
    return sp

  def Parse():
    while .t:
      .ParseStanza()
    return self

  def ParseStanza():
    .MustT('Header')
    name = FRONT_HEADER.FindString(.v)
    name = name[1:-1]  # Trim the brackets.
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
    .Advance()

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
      say 'dog', .v
      say 'dog', str(.v)
      s = .v
      s = QUOTE0.ReplaceAllString(s, '')
      s = QUOTE1.ReplaceAllString(s, '')
      s = QUOTE2.ReplaceAllString(s, '')
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
      z.append(.ParseExpr())
    return List(z)


  def MustT(t):
    if .t != t:
      .Bad('Expected %s, got %s: %s' % (t, .t, .v))

Interned = {}

def Intern(s):
  assert type(s) == str
  sym = Interned.get(s)
  if sym is None:
    sym = Symbol(s)
    Interned[s] = sym
  return sym

Prim = Intern("prim")
Lambda = Intern("lamdba")
Quote = Intern("quote")
Nil = Intern("nil")
T = Intern("true")
F = Intern("false")

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
      return '"%s"' % .x  # TODO: fix for escaping.
    else:
      return repr(.x)
  def Eval(env, stanza):
    return self

class Symbol(Node):
  def __init__(s):
    .s = s
  def Show():
    return .s
  def Lookup(env, stanza):
    for k, v in env:
      if .Eq(k):
        return v
    if stanza:
      return stanza.Lookup(self)
  def Eval(env, stanza):
    st = stanza
    ww = strings.Split(.s, '.')
    for w in ww[:-1]:
      st = st.X
    return .Lookup(env, stanza)


class List(Node):
  def __init__(v):
    .v = v

  def Len():
    return len(.v)

  def Show():
    z = '('
    for x in .v:
      if len(z) > 1:
        z += ' '
      z += x.Show()
    return z + ')'

  def Eval(env, stanza):
    if len(.v) < 1:
      return self
    hd = .v[0]

    # Special Forms:
    if hd is Lambda:
      return self
    if hd is Prim:
      return self
    if hd is Quote:
      return .v[1]

    cmd = hd.Eval(env, stanza)
    if type(cmd) is List:
      if len(cmd.v) == 3 and cmd.v[0] is Lambda and type(cmd.v[1]) is List:
        formals = cmd.v[1]
        expr = cmd.v[2]
        if len(formals.v) == len(.v) - 1:
          env2 = env
          for i in range(len(formals)):
            env2 = [(formals[i], cmd.v[i+1].Eval(env, stanza))] + env2
            return expr.Eval(env2, stanza)
        else:
          raise 'Wrong number of formals (%s) vs args (%s)' % (len(formals.v), len(.v) - 1)

      if len(cmd.v) == 2 and cmd.v[0] is Prim:
        primName = cmd.v[1].x
        fn = PRIMS.get(primName)
        if not fn:
          raise 'Prim does not exist: %q' % primName
        return fn(self, env, stanza)

      raise 'Strange list in head position is not valid lambda expr: %s' % cmd.v.Show()
    raise 'Other: %s' % .Show()

PRIMS = {}

def PrimList(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x + c.x )
PRIMS['plus'] = PrimPlus

def args(a, env, stanza):
  say a
  say a.Show()
  say a.v
  tl = a.v[1:]
  return [x.Eval(env, stanza) for x in tl]

def arg2(a, env, stanza):
  assert len(a.v) == 3
  return args(a, env, stanza)

def PrimPlus(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x + c.x )
PRIMS['plus'] = PrimPlus

def PrimMinus(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x - c.x )
PRIMS['minus'] = PrimMinus

def PrimTimes(a, env, stanza):
  b, c = arg2(a, env, stanza)
  return Lit( b.x * c.x )
PRIMS['times'] = PrimTimes

#e = Engine(' [Abc] a = "foo" [Def] b = "bar" [Ghi.Xyz] ')
#e.Parse()
#say e.stanzas
#say e.stanzas['Abc'].slots['a']
#z = Engine('[x] y = ( add 34 "23" )').Parse().stanzas['x'].slots['y']
#say z
#say z.Show()
#assert z.Len() == 3, z
#
#prim_plus__21__2 = List([ List([ Intern('prim'), Lit('plus') ]), Lit(21), Lit(2) ])
#x = prim_plus__21__2.Eval( [], None )
#assert 23 == x.x
#assert type(Prim) is Symbol
#assert type(prim_plus__21__2) is List
#assert type(x) is Lit
#assert type(x.x) is int
#say Symbol
#say str(Symbol)
#say repr(Symbol)

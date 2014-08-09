
#from go import fmt
#from go import html
#from go import io/ioutil
#from go import net/http
#from go import net/url
from go import regexp
#from go import time

WORD = regexp.MustCompile('([A-Za-z])([A-Za-z0-9_]+)')
WORDS = regexp.MustCompile('(([A-Za-z])([A-Za-z0-9_]+))([.](([A-Za-z])([A-Za-z0-9_]+))*)')
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

print "word", WORD
print WORD.Find("345 Foo777 bar ")
print WORD.FindString("345 Foo777 bar ")
print WORD.FindAllString("345 Foo777 bar ", -1)
print WORD.FindAllStringIndex("345 Foo777 bar ", -1)
print 'last', WORD.FindAll("345 Foo777 bar ", -1)

print 'FRONT_HEADER.FindString', FRONT_HEADER.FindString('[abc] xxx')
assert FRONT_HEADER.FindString('[abc] xxx') == '[abc]'

assert WORDS.FindString('FooBar.Baz')
assert not FRONT_WORDS.FindString(' FooBar.Baz')
print 'OKAY'

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
  def __init__(self, engine):
    .name = None
    .up = None
    .slots = {}
    .engine = engine

        
class Engine:
  def __init__(self, text):
    .stanzas = {}
    .text = text
    .toks = list(Tokenize(text))
    .n = len(.toks)
    .p = -1
    .Advance()

  def Advance(self):
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

  def MakeStanza(self, s):
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

  def Parse(self):
    while .t:
      .ParseStanza()
    return self

  def ParseStanza(self):
    .MustT('Header')
    name = FRONT_HEADER.FindString(.v)
    name = name[1:-1]  # Trim the brackets.
    stanza = .MakeStanza(name)
    .Advance()

    while .t == 'Words':
      .ParseSlot(stanza)

  def ParseSlot(self, stanza):
    k = .v
    .Advance()

    .MustT('Eq')
    .Advance()

    v = .ParseExpr()
    stanza.slots[k] = v
    .Advance()

  def ParseExpr(self):
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
      z = Lit(str(.v))
      .Advance()
      return z
    if .t == 'Quote':
      .Advance()
      x = .ParseExpr()
      return List([Intern('quote'), x])
    raise 'ParseExpr unknown: %s: %d' % (.t, .v)
      
  def ParseList(self):
    .MustT('Open')
    .Advance()
    z = []
    while .t != 'Close':
      z.append(.ParseExpr())
    return List(z)
      

  def MustT(self, t):
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

class Node:
  def __init__(self):
    pass

class Lit(Node):
  def __init__(self, x):
    .x = x
  def Eq(self, a):
    return self is a
  def Show(self):
    if type(.x) == str:
      return '"%s"' % .x  # TODO: fix for escaping.
    else:
      return repr(.x)

class Symbol(Node):
  def __init__(self, s):
    .s = s
  def Show(self):
    return .s
  def Lookup(self, env, stanza):
    for k, v in env:
      if .Eq(k):
        return v
    if stanza:
      return stanza.Lookup(self)
    

class List(Node):
  def __init__(self, v):
    .v = v
  def Eq(self, a):
    return False
  def Len(self):
    return len(.v)
  def Show(self):
    z = '('
    for x in .v:
      if len(z) > 1:
        z += ' '
      z += x.Show()
    return z + ')'

e = Engine(' [Abc] a = "foo" [Def] b = "bar" [Ghi.Xyz] ')
e.Parse()
say e.stanzas
say e.stanzas['Abc'].slots['a']
z = Engine('[x] y = ( add 34 "23" )').Parse().stanzas['x'].slots['y']
say z
say z.Show()
assert z.Len() == 3, z

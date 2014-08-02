
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
    self.name = None
    self.up = None
    self.slots = {}
    self.engine = engine

  def Lookup(self, key):
    z = self.slots.get(key)
    if z:
      return z
    else:
      if self.slots.up:
        return self.slots.up.Lookup(key)
      else:
        return None
        
class Engine:
  def __init__(self, text):
    self.stanzas = {}
    self.text = text
    self.toks = list(Tokenize(text))
    self.n = len(self.toks)
    self.p = -1
    self.Advance()

  def Advance(self):
    if self.p >= self.n:
      self.t = None
      self.v = None
      return

    self.p += 1
    if self.p >= self.n:
      self.t = None
      self.v = None
      return
    self.t = self.toks[self.p][0]
    self.v = self.toks[self.p][1]

  def MakeStanza(self, s):
    sp = self.stanzas.get(s)
    if not sp:
      sp = Stanza(self)
      sp.name = s
      m = PARENT.FindStringSubmatch(s)
      self.stanzas[sp.name] = sp
      if m:
        print 'm: ', m
        sp.up = self.MakeStanza(m[1])
    return sp

  def Parse(self):
    while self.t:
      self.ParseStanza()
    return self

  def ParseStanza(self):
    self.MustT('Header')
    name = FRONT_HEADER.FindString(self.v)
    name = name[1:-1]  # Trim the brackets.
    stanza = self.MakeStanza(name)
    self.Advance()

    while self.t == 'Words':
      self.ParseSlot(stanza)

  def ParseSlot(self, stanza):
    k = self.v
    self.Advance()

    self.MustT('Eq')
    self.Advance()

    v = self.ParseExpr()
    stanza.slots[k] = v
    self.Advance()

  def ParseExpr(self):
    if not self.t:
      raise "Expected expression but got End of String."
    if self.t == 'Open':
      return self.ParseList()
    if self.t == 'Words':
      z = Intern(str(self.v))
      self.Advance()
      return z
    if self.t == 'Int':
      z = Lit(int(self.v))
      self.Advance()
      return z
    if self.t == 'Float':
      z = Lit(float(self.v))
      self.Advance()
      return z
    if self.t == 'Str':
      z = Lit(str(self.v))
      self.Advance()
      return z
    if self.t == 'Quote':
      self.Advance()
      x = self.ParseExpr()
      return List([Intern('quote'), x])
    raise 'ParseExpr unknown: %s: %d' % (self.t, self.v)
      
  def ParseList(self):
    self.MustT('Open')
    self.Advance()
    z = []
    while self.t != 'Close':
      z.append(self.ParseExpr())
    return List(z)
      

  def MustT(self, t):
    if self.t != t:
      self.Bad('Expected %s, got %s: %s' % (t, self.t, self.v))

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
    self.x = x
  def Eq(self, a):
    return self is a
  def Show(self):
    if type(self.x) == str:
      return '"%s"' % self.x  # TODO: fix for escaping.
    else:
      return repr(self.x)
  def Eval(self, env, stanza):
    return self

class Symbol(Node):
  def __init__(self, s):
    self.s = s
  def Show(self):
    return self.s
  def Lookup(self, env, stanza):
    for k, v in env:
      if self.Eq(k):
        return v
    if stanza:
      return stanza.Lookup(self)
  def Eval(self, env, stanza):
    return self.Lookup(env, stanza)
    

class List(Node):
  def __init__(self, v):
    self.v = v
  def Eq(self, a):
    return False
  def Len(self):
    return len(self.v)
  def Show(self):
    z = '('
    for x in self.v:
      if len(z) > 1:
        z += ' '
      z += x.Show()
    return z + ')'
  def Eval(self, env, stanza):
    return 'TODO zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz'

e = Engine(' [Abc] a = "foo" [Def] b = "bar" [Ghi.Xyz] ')
e.Parse()
say e.stanzas
say e.stanzas['Abc'].slots['a']
z = Engine('[x] y = ( add 34 "23" )').Parse().stanzas['x'].slots['y']
say z
say z.Show()
assert z.Len() == 3, z

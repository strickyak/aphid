
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
FRONT_WORDS = regexp.MustCompile('^(([A-Za-z_])([A-Za-z0-9_]+))([.](([A-Za-z_])([A-Za-z0-9_]+)))*')
FRONT_STANZA = regexp.MustCompile('^[[]((([A-Za-z])([A-Za-z0-9_]+))([.](([A-Za-z])([A-Za-z0-9_]+)))*)[]]')
FRONT_OPEN = regexp.MustCompile('^[(]')
FRONT_CLOSE = regexp.MustCompile('^[)]')
FRONT_QUOTE = regexp.MustCompile("^[']")
FRONT_STRING = regexp.MustCompile('^"([^"]|"")*"')
FRONT_INT = regexp.MustCompile('^[-]?[0-9]+')
FRONT_FLOAT = regexp.MustCompile('^[-]?[0-9]+[.]?[0-9]+')  # No exponential notation.

L2 = [ ('Open', FRONT_OPEN), ('Close', FRONT_CLOSE), ('Quote', FRONT_QUOTE), ('String', FRONT_STRING) ]
LEXERS = [ ('Eq', FRONT_EQ), ('Words', FRONT_WORDS), ('Stanza', FRONT_STANZA) ] + L2

print "word", WORD
print WORD.Find("345 Foo777 bar ")
print WORD.FindString("345 Foo777 bar ")
print WORD.FindAllString("345 Foo777 bar ", -1)
print WORD.FindAllStringIndex("345 Foo777 bar ", -1)
print 'last', WORD.FindAll("345 Foo777 bar ", -1)

print 'FRONT_STANZA.FindString', FRONT_STANZA.FindString('[abc] xxx')
assert FRONT_STANZA.FindString('[abc] xxx') == '[abc]'

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
  def __init__(self):
    self.name = None
    self.up = None
    self.slots = {}

        
class LaphEngine:
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
      sp = Stanza()
      sp.name = s
      m = PARENT.FindStringSubmatch(s)
      self.stanzas[sp.name] = sp
      if m:
        print 'm: ', m
        sp.up = self.MakeStanza(m[1])
    return sp

  def ParseAll(self):
    while self.t:
      if self.t != 'Stanza':
        self.Bad('Expected stanza, got %s: %s' % (self.t, self.v))
      print 'self.v', self.v
      s = FRONT_STANZA.FindString(self.v)
      s = s[1:-1]  # Trim the brackets.
      sp = self.MakeStanza(s)
      self.Advance()
    return
pass

e = LaphEngine(" [Abc] [Def] [Ghi.Xyz] ")
e.ParseAll()
say e.stanzas

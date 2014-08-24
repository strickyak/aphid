from go import regexp
from go import strconv

RE_WHITE = regexp.MustCompile('^([#][^\n]*[\n]|[ \t\n]+)*')

RE_KEYWORDS = regexp.MustCompile('^\\b(None|null|nil|True|False)\\b')
RE_PUNCT = regexp.MustCompile('^[][(){}:,]')
RE_ALFA = regexp.MustCompile('^[A-Za-z_][A-Za-z0-9_]*')
RE_FLOAT = regexp.MustCompile('^[+-]?[0-9][-+0-9eE]*[.eE][-+0-9eE]*')
RE_INT = regexp.MustCompile('^[+-]?[0-9]+')
RE_STR = regexp.MustCompile('^(["](([^"\\\\\n]|[\\\\].)*)["]|[\'](([^\'\\\\\n]|[\\\\].)*)[\'])')

DETECTERS = [ (RE_KEYWORDS, 'K'), (RE_FLOAT, 'F'), (RE_INT, 'N'), (RE_PUNCT, 'G'), (RE_STR, 'S'), ]

def Eval(s):
  ep = EvalParser(s)
  k, x = ep.Token()
  z = ep.Parse(k, x)
  ep.Skip()
  if ep.p != ep.n:
    raise 'Eval: Leftover chars', ep.s[ep.p:], z
  return z

class EvalParser:
  def __init__(s):
    .s = s
    .n = len(s)
    .p = 0

  def Skip():
    w = RE_WHITE.FindString(.s[.p:])
    .p += len(w)

  def Token():
    .Skip()
    if .p == .n:
      say 'Token', None, None
      return None, None
    for r, k in DETECTERS:
      m = r.FindString(.s[.p:])
      if m:
        .p += len(m)
        say 'Token', k, m
        return k, m
    raise 'eval.EvalParser: Cannot Parse', .s[.p:], .s

  def Parse(k, x):
    if not k:
      raise 'eval.EvalParser: Unexpected end of string', .s
    if k == 'K':
      if x[0] in ['n', 'N']:
        return None
      if x[0] in ['t', 'T']:
        return True
      if x[0] in ['f', 'F']:
        return False
      raise 'eval.EvalParser: Weird token', x, .s
    if k == 'N':
      say strconv.ParseInt(x, 10, 64)
      return strconv.ParseInt(x, 10, 64)
    if k == 'F':
      say strconv.ParseFloat(x, 64)
      return strconv.ParseFloat(x, 64)
    if k == 'S':
      return Unquote(x)
    if x == '[':
      v = []
      while True:
        k2, x2 = .Token()
        if not k2:
          raise 'eval.EvalParser: Unexpected end of string', .s
        if x2 == ']':
          break
        if x2 == ',':
          continue
        a = .Parse(k2, x2)
        v.append(a)
      return v
    if x == '(':
      v = []
      while True:
        k2, x2 = .Token()
        if not k2:
          raise 'eval.EvalParser: Unexpected end of string', .s
        if x2 == ')':
          break
        if x2 == ',':
          continue
        a = .Parse(k2, x2)
        v.append(a)
      return tuple(v)
    if x == '{':
      d = {}
      while True:
        k2, x2 = .Token()
        if not k2:
          raise 'eval.EvalParser: Unexpected end of string', .s
        if x2 == '}':
          break
        if x2 == ',':
          continue

        a = .Parse(k2, x2)

        k2, x2 = .Token()
        if x2 != ':':
          raise 'eval.EvalParser: expected ":" after key'

        k2, x2 = .Token()
        b = .Parse(k2, x2)

        d[a] = b
      return d
    raise 'eval.EvalParser: Weird token', k, x

def Unquote(a):
  # TODO -- unescape
  if a[0] == a[-1]:
    return a[1:-1]
  raise 'eval.Unquote: bad input', a

assert Eval('True') is True
assert Eval('False') is False
assert Eval('None') is None

assert Eval('12345') == 12345
assert Eval('-12345') == -12345
assert Eval('-1234.5') == -1234.5

assert Eval('[ 123, 4.5, False] ') == [ 123, 4.5, False]
# TODO: DiCT::EQ  # assert Eval('{ "color": "red", "area": 51 } ') == { "color": "red", "area": 51 }

d = Eval('{ "color": "red", "area": 51 } ')
e = { "color": "red", "area": 51 }

assert [(k, d[k]) for k in d] == [(k, e[k]) for k in e]

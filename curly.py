from go import fmt, regexp, unicode/utf8

def ORD(c):
  """ORD() is Like ord() but works on utf8 runes."""
  native:
    'x := rune(0)'
    'n, err := fmt.Sscanf(a_c.String(), "%c", &x)'
    'if err != nil { panic(err) }'
    'if n != 1 { panic("fmt.Sscanf fails") }'
    'return Mkint(int(x))'

RE_UNSTRONG_CHARS = regexp.MustCompile('[^-A-Za-z0-9_.]')
def StrongCurlyEncode(s):
  """Encode using a narrow set of chars, for instance for filenames."""
  if s:
    s = str(s)
    must utf8.ValidString(s)
    return RE_UNSTRONG_CHARS.ReplaceAllStringFunc(s, lambda c: '{%d}' % ORD(c))
  else:
    return '{}'

RE_UNWEAK_CHARS = regexp.MustCompile('[^!-z|~]')
def WeakCurlyEncode(s):
  """Encode using printable ASCII chars, avoiding space, control chars, and non-ascii unicode."""
  if s:
    s = str(s)
    must utf8.ValidString(s)
    return RE_UNWEAK_CHARS.ReplaceAllStringFunc(s, lambda c: '{%d}' % ORD(c))
  else:
    return '{}'

RE_CURLIED = regexp.MustCompile('{[0-9]+}')
def CurlyDecode(s):
  """Decode either StrongCurlyEncode() or WeakCurlyEncode()."""
  must s
  s = str(s)
  if s == '{}':
    return ''
  else:
    return RE_CURLIED.ReplaceAllStringFunc(s, lambda x: fmt.Sprintf('%c', int(x[1:-1])))

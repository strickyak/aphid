from go import encoding/base64, encoding/ascii85
from go import encoding/hex as H 
from go import fmt, regexp, unicode/utf8, crypto/md5

##
##  Double-MD5 Hash
##

def DoubleMD5(pw):
  """Double MD5 with newlines and hexing."""
  hashed = '%x' % md5.Sum('%s\n' % pw)
  hashed2 = '%x' % md5.Sum('%s\n' % hashed)
  return hashed2

##
##  Base85
##

def Encode85(b):
  b = byt(b)
  z = mkbyt(ascii85.MaxEncodedLen(len(b)))
  c = ascii85.Encode(z, b)
  return z[:c]

def Decode85(b):
  b = byt(b)
  z = mkbyt(len(b))
  c, _ = ascii85.Decode(z, b, True)
  return z[:c]

##
##  Base64
##

BASE_64 = base64.URLEncoding

def Encode64(b):
  return BASE_64.EncodeToString(b)

def Decode64(s):
  return BASE_64.DecodeString(s)

##
##  Hex
##

RE_HEX = regexp.MustCompile('^[0-9a-f]*$').FindStringIndex

def DecodeHex(s):
  must RE_HEX(s), repr(s)
  must len(s) & 1 == 0, len(s)  # Even length.
  z = mkbyt(len(s)/2)
  H.Decode(z, s)
  return z

def EncodeHex(b):
  z = mkbyt(len(b)*2)
  H.Encode(z, b)
  return str(z)


##
##  Curly
##

def FirstRuneOrd(s):
  """FirstRuneOrd() is Like ord() but works on the first utf8 rune."""
  native: `
    for _, ru := range a_s.String() {
      return Mkint(int(ru))
    }
  `

RE_UNSTRONG_CHARS = regexp.MustCompile('[^-A-Za-z0-9_.]')
def EncodeCurlyStrong(s):
  """Encode using a narrow set of chars, for instance for filenames."""
  if s:
    s = str(s)
    must utf8.ValidString(s)
    return RE_UNSTRONG_CHARS.ReplaceAllStringFunc(s, lambda c: '{%d}' % FirstRuneOrd(c))
  else:
    return '{}'

RE_UNWEAK_CHARS = regexp.MustCompile('[^!-z|~]')
def EncodeCurlyWeak(s):
  """Encode using printable ASCII chars, avoiding space, control chars, and non-ascii unicode."""
  if s:
    s = str(s)
    must utf8.ValidString(s)
    return RE_UNWEAK_CHARS.ReplaceAllStringFunc(s, lambda c: '{%d}' % FirstRuneOrd(c))
  else:
    return '{}'

RE_CURLIED = regexp.MustCompile('{[0-9]+}')
def DecodeCurly(s):
  """Decode either StrongCurlyEncode() or WeakCurlyEncode()."""
  must s
  s = str(s)
  if s == '{}':
    return ''
  else:
    return RE_CURLIED.ReplaceAllStringFunc(s, lambda x: fmt.Sprintf('%c', int(x[1:-1])))

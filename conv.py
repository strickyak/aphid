from go import fmt, regexp, unicode/utf8
from go import crypto/sha256
from go import encoding/base64, encoding/ascii85
from go import encoding/hex as H 

##
##  Double Hash
##

# You can verify DoubleHash with the linux sha256sum command:
# $ conv/conv DoubleHash one two
# 7306633bc4e3daa2f4a2883b03fca1e44bbb0746635daf73263233f13e055b76
# $ echo DoubleHash:one:two | sha256sum
# 290d0000d2bf5d44ff3a1c17f4a87f4086b296e99a3ef0cb32859b23040eeedb -
# $ echo DoubleHash:290d0000d2bf5d44ff3a1c17f4a87f4086b296e99a3ef0cb32859b23040eeedb:two | sha256sum 
# 7306633bc4e3daa2f4a2883b03fca1e44bbb0746635daf73263233f13e055b76  -
def DoubleHash(pw, salt):
  """Double Hash with newlines and hexing."""
  t = '%x' % sha256.Sum256('DoubleHash:%s:%s\n' % (pw, salt))
  return '%x' % sha256.Sum256('DoubleHash:%s:%s\n' % (t, salt))

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
    for _, ru := range a_s.Self.String() {
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

def main(args):
  cmd = args.pop(0)
  if cmd == 'DoubleHash':
    pw = args.pop(0)
    salt = args.pop(0)
    print DoubleHash(pw, salt)

from go import encoding/hex, regexp
from go/crypto import aes, cipher, rand

# Standardize key size.
KEY_BYT_LEN = 32
KEY_HEX_LEN = 64

RE_HEX = regexp.MustCompile('^[0-9a-f]+$').FindString

def DecodeHex(s):
  must RE_HEX(s)
  must len(s) == KEY_HEX_LEN
  z = mkbyt(KEY_BYT_LEN)
  hex.Decode(z, s)
  return z

def EncodeHex(b):
  must type(b) == byt
  must len(b) == KEY_BYT_LEN
  z = mkbyt(KEY_HEX_LEN)
  hex.Decode(z, b)
  return str(z)

class Cipher:
  def __init__(key):
    """Construct a Cipher with a byt key with len KEY_BYT_LEN."""
    must type(key) is byt
    must len(key) == KEY_BYT_LEN

    .block = aes.NewCipher(key)
    #say .block
    .gcm = cipher.NewGCM(.block)
    #say .gcm
    .nonceSize = int(.gcm.NonceSize())
    .overhead = int(.gcm.Overhead())

  def Nonce():
    buf = mkbyt(.nonceSize)
    rand.Read(buf)  # Uses ReadFull.
    return buf

  def Seal(plain, serial):
    extra = rye_pickle(serial)
    nonce = .Nonce()
    dark = .gcm.Seal(None, nonce, plain, extra)
    return rye_pickle( (nonce, dark, extra) )

  def Open(sealed):
    nonce, dark, extra = rye_unpickle(sealed)
    plain = .gcm.Open(None, nonce, dark, extra)
    serial = rye_unpickle(extra)
    return plain, serial

def main(argv):
  key = 'ABCDEFGHabcdefgh'
  c = Cipher(key)
  plain = 'I wish I were an Oscar Meyer Wiener.'
  serial = ('nando', 3.14159)
  say plain, serial
  sealed = c.Seal(plain, serial)
  say sealed
  recovered, extra = c.Open(sealed)
  say recovered, extra
  must (str(recovered), extra) == (plain, serial)
  say c.gcm.Overhead()
  say c.gcm.NonceSize()

  for k in range(5000):
    n = k+1
    plain = mkbyt(n)
    nonce = c.Nonce()
    x = c.gcm.Seal(None, nonce, plain, "extra")
    y = c.gcm.Open(None, nonce, x, "extra")
    must y == plain
    must len(x)-n == c.gcm.Overhead()
    # say n, len(x), len(x)-n
  say "gcm OKAY."

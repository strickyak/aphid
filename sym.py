from go import encoding.hex, regexp
from go.crypto import aes, cipher, rand

# Standardize key size.
KEY_BYT_LEN = 32
KEY_HEX_LEN = 64

RE_HEX = regexp.MustCompile('^[0-9a-f]+$').FindString

def RandomKey() ::byt:
  bb = mkbyt(KEY_BYT_LEN)
  c = rand.Read(bb)
  must c == KEY_BYT_LEN
  return bb

def DecodeHex(s :str) ::byt:
  must RE_HEX(s)
  must len(s) == KEY_HEX_LEN
  z = mkbyt(KEY_BYT_LEN)
  hex.Decode(z, s)
  return z

def EncodeHex(b :byt) ::str:
  must type(b) == byt
  must len(b) == KEY_BYT_LEN
  z = mkbyt(KEY_HEX_LEN)
  hex.Encode(z, b)
  return str(z)

class Cipher:
  def __init__(key ::byt):
    """Construct a Cipher with a byt key with len KEY_BYT_LEN."""
    must type(key) is byt
    must len(key) == KEY_BYT_LEN

    .block = aes.NewCipher(key)
    .gcm = cipher.NewGCM(.block)
    .nonceSize = int(.gcm.NonceSize())
    .overhead = int(.gcm.Overhead())

  def Nonce() ::byt:
    buf = mkbyt(.nonceSize)
    rand.Read(buf)  # Uses ReadFull.
    return buf

  def Seal(plain, serial) ::byt:
    extra = rye_pickle(serial)
    nonce = .Nonce()
    dark = .gcm.Seal(None, nonce, plain, extra)
    z = rye_pickle( (nonce, dark, extra) )
    return z

  def Open(sealed ::byt) ::tuple:
    nonce, dark, extra = rye_unpickle(sealed)
    plain = .gcm.Open(None, nonce, dark, extra)
    serial = rye_unpickle(extra)
    return plain, serial

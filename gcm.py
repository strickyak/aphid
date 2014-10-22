from go import crypto/aes
from go import crypto/cipher
from go import crypto/rand

KEY_SIZES = [16, 24, 32]

class Cipher:
  def __init__(key):
    key = byt(key)
    must len(key) in KEY_SIZES, len(key)
    .block = aes.NewCipher(key)
    say .block
    .gcm = cipher.NewGCM(.block)
    say .gcm
    .nonceSize = int(.gcm.NonceSize())
    .overhead = int(.gcm.Overhead())

  def Nonce():
    buf = byt(.nonceSize)
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

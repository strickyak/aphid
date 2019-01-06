from go import encoding.hex, regexp
from go.crypto import aes, cipher, rand

import sym

def main(_):
  key = byt(4 * 'ABCDEFGH')
  c = sym.Cipher(key)
  plain = 'I wish I were an Oscar Meyer Wiener.'
  serial = ('nando', 3.14159)
  say plain, serial
  sealed = c.Seal(plain, serial)
  say sealed
  recovered, extra = c.Open(sealed)
  must (recovered, extra) == (byt('I wish I were an Oscar Meyer Wiener.'), ('nando', 3.14159))
  must (str(recovered), extra) == (plain, serial)
  must 16 == c.gcm.Overhead()
  must 12 == c.gcm.NonceSize()

  for k in range(5000):
    n = k+1
    plain = mkbyt(n)
    nonce = c.Nonce()
    x = c.gcm.Seal(None, nonce, plain, 'extra')
    y = c.gcm.Open(None, nonce, x, 'extra')
    must y == plain
    must len(x)-n == c.gcm.Overhead()

  say 'gcm OKAY.'

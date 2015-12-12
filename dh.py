from go import math/big
from go import crypto/rand as crand
from . import conv

def Big(s :str|byt):
  must s
  return big.NewInt(0).SetBytes(conv.Decode64(s))

def String(x):
  must x
  must go_typeof(x).String() == '*big.Int'
  return conv.Encode64(x.Bytes())

def DefineGroup(sz, g, m):
  # Drop all non-upper-hex chars from string m.
  m = ''.join([c for c in m if '0'<= c <='9' or 'A'<= c <='F'])
  # g is a small int, but m is a large hexadecimal string.
  generator = big.NewInt(g)
  modulus, ok = big.NewInt(0).SetString(m, 16)
  must ok
  return sz, generator, modulus

def CryptoRandBig(m):
  # big.Int::Rand() insists on insecure math.rand!
  # So we'll forge our number with crand.
  # These are not evenly distributed, because we generate
  # bytes that may be bigger than m, and fold them down with Mod.
  # But this bias is cryptographically insiginificant.
  n = len(m.Bytes())
  bb = mkbyt(n)
  c = crand.Read(bb)
  must c == n
  z = big.NewInt(0).SetBytes(bb)
  return big.NewInt(0).Mod(z, m)

def Forge(group):
  sz, g, m = group
  sec = CryptoRandBig(m)
  pub = big.NewInt(0).Exp(g, sec, m)
  return DhSecret(group, pub, sec)

class DhSecret:
  def __init__(group, pub, sec):
    must type(pub) != str, '%T' % pub
    must type(sec) != str, '%T' % sec
    .sz, .g, .m = group
    .pub = pub
    .sec = sec

  def Public():
    return String(.pub)

  def Secret():
    return String(.sec)

  def MutualKey(their_pub):
    p = Big(their_pub)
    z = big.NewInt(0).Exp(p, .sec, .m)
    # Drop last 8 bytes, then return last 32.
    return z.Bytes()[-40:-8]

G1536 = DefineGroup(1536, 2, '''
      FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1
      29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD
      EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245
      E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED
      EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D
      C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F
      83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D
      670C354E 4ABC9804 F1746C08 CA237327 FFFFFFFF FFFFFFFF
''')

G2048 = DefineGroup(2048, 2, '''
      FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1
      29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD
      EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245
      E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED
      EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D
      C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F
      83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D
      670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B
      E39E772C 180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9
      DE2BCBF6 95581718 3995497C EA956AE5 15D22618 98FA0510
      15728E5A 8AACAA68 FFFFFFFF FFFFFFFF
''')

G3072 = DefineGroup(3072, 2, '''
      FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1
      29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD
      EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245
      E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED
      EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D
      C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F
      83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D
      670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B
      E39E772C 180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9
      DE2BCBF6 95581718 3995497C EA956AE5 15D22618 98FA0510
      15728E5A 8AAAC42D AD33170D 04507A33 A85521AB DF1CBA64
      ECFB8504 58DBEF0A 8AEA7157 5D060C7D B3970F85 A6E1E4C7
      ABF5AE8C DB0933D7 1E8C94E0 4A25619D CEE3D226 1AD2EE6B
      F12FFA06 D98A0864 D8760273 3EC86A64 521F2B18 177B200C
      BBE11757 7A615D6C 770988C0 BAD946E2 08E24FA0 74E5AB31
      43DB5BFC E0FD108E 4B82D120 A93AD2CA FFFFFFFF FFFFFFFF
''')

# Standardize Aphid's group.
GROUP = G3072
pass

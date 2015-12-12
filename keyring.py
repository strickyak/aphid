from go import bytes, encoding/hex, fmt, io/ioutil, regexp
from go/crypto import rand, sha256
from . import conv, dh, flag, sym
from lib import data

"The global RingDict."
RingDict = {}
Ring = {}

RingFilename = flag.String('ring', '', 'name of keyring file')
RingSecret = flag.String('secret', '', 'passphrase of keyring file')

RE_HEX = regexp.MustCompile('^[0-9a-f]+$').FindString
RE_BASE64 = regexp.MustCompile('^[-A-Za-z0-9_=]+$').FindString

SavedSecretCipher = None
def LazySecretCipher():
  if not SavedSecretCipher:
    SavedSecretCipher = sym.Cipher(sha256.Sum256(RingSecret.X))
  return SavedSecretCipher

def SealWithSecret(plain):
  return conv.Encode64(LazySecretCipher().Seal(plain, 'WithSecret'))

def OpenWithSecret(encrypted):
  plain, serial = LazySecretCipher().Open(conv.Decode64(encrypted))
  must serial == 'WithSecret'
  return plain

class DhKey:
  def __init__(d):
    say d
    .id = d['id']
    .pub = d['pub']
    .sec = d.get('sec') if d.get('sec') else OpenWithSecret(d['Xsec']) if d.get('Xsec') else None
    must RE_BASE64(.pub)
    .o_pub = dh.Big(.pub)  # big.Int
    if .sec:
      must RE_BASE64(.sec)
      .o_sec = dh.DhSecret(group=dh.GROUP, pub=.o_pub, sec=dh.Big(.sec))  # DhSecret

class SymKey:
  def __init__(d):
    .id = d['id']
    .num = d['num']
    .sym = d['sym'] if d.get('sym') else conv.EncodeHex(OpenWithSecret(d['Xsym']))
    must RE_HEX(.sym)
    must len(.sym)== sym.KEY_HEX_LEN
    .b_sym = sym.DecodeHex(.sym)

class WebKey:
  def __init__(d):
    .id = d['id']
    .num = d['num']
    .xor = d['xor'] if d.get('xor') else OpenWithSecret(d['Xxor'])
    .base = d['base']
    say .id, .xor, .base, d
    must RE_HEX(.xor)
    must len(.xor)== sym.KEY_HEX_LEN
    .b_xor = sym.DecodeHex(.xor)

class HashedPw:
  def __init__(d):
    .id = d['id']
    .doubleHash = d['doubleHash'] if d.get('doubleHash') else OpenWithSecret(d['XdoubleHash'])
    .salt = d['salt']

def CompileDicts(d):
  """CompileDicts the dict of dicts into the dict of objects."""
  ring = {}
  say d
  for k, v in d.items():
    say k, v
    switch v['TYPE']:
      case 'pw/doubleHash':
        ring[k] = HashedPw(v)
      case 'dh':
        ring[k] = DhKey(v)
      case 'sym/aes256':
        ring[k] = SymKey(v)
      case 'web/aes256':
        ring[k] = WebKey(v)
      default:
        raise 'Unknown Type', v['TYPE']
  return ring

def Load(filename=None):
  """Load the ring dict from the file."""
  global RingDict, Ring
  filename = filename if filename else RingFilename.X
  say 'Loading Keyring', filename
  s = str(ioutil.ReadFile(filename)).strip()
  if s:
    RingDict = data.Eval(s)
  else:
    RingDict = {}
  Ring = CompileDicts(RingDict)

def Save(filename=None):
  """Save the ring dict to the file."""
  filename = filename if filename else RingFilename.X
  for k, v in RingDict.items():
    print '=====', k, '====='
    print v
  print '====='
  Ring = CompileDicts(RingDict)
  ioutil.WriteFile(filename, data.PrettyPrint(RingDict), 0600)

def main(args):
  args = flag.Munch(args)
  Load(None)   # TODO local bug
  if args:
    cmd = args.pop(0)

  say cmd, args
  switch cmd:
    case "nop":
      pass

    case "mkpw":
      key_id = args.pop(0)
      pw = args.pop(0)
      hex_salt = conv.EncodeHex(sym.RandomKey())
      RingDict[key_id] = dict(
          id=key_id,
          TYPE='pw/doubleHash',
          salt=hex_salt,
          doubleHash=None if RingSecret.X else conv.DoubleHash(pw, hex_salt),
          XdoubleHash=SealWithSecret(conv.DoubleHash(pw, hex_salt)) if RingSecret.X else None,
          )

    case "mkdh":
      key_id = args.pop(0)
      must not args

      pair = dh.Forge(group=dh.GROUP)
      RingDict[key_id] = dict(
          id=key_id,
          TYPE='dh',
          pub=dh.String(pair.pub),
          sec=None if RingSecret.X else dh.String(pair.sec),
          Xsec=SealWithSecret(dh.String(pair.sec)) if RingSecret.X else None,
          )

    case "mksym":
      key_id = args.pop(0)
      key_num = args.pop(0)
      must not args

      bb = sym.RandomKey()
      say RingDict
      say key_id, key_num, bb
      RingDict[key_id] = dict(
          num=key_num,
          id=key_id,
          TYPE='sym/aes256',
          sym=None if RingSecret.X else conv.EncodeHex(bb),
          Xsym=SealWithSecret(bb) if RingSecret.X else None,
          )
      say RingDict

    case "mkweb":
      # First find the base key.
      # Then use "mkweb" to make the derived web key.
      # Do not publish the base key.
      key_id = args.pop(0)
      key_num = args.pop(0)
      key_base = args.pop(0)
      pw = args.pop(0)

      must not args
      base = Ring[key_base]
      basekey = base.b_sym
      say basekey

      pwhash = sha256.Sum256(pw)
      say pwhash
      assert len(pwhash) == sym.KEY_BYT_LEN

      xorkey = basekey ^ pwhash
      say xorkey
      assert len(xorkey) == sym.KEY_BYT_LEN

      RingDict[key_id] = dict(
          num=key_num,
          id=key_id,
          base=key_base,
          TYPE='web/aes256',
          xor=None if RingSecret.X else conv.EncodeHex(xorkey),
          Xxor=SealWithSecret(xorkey) if RingSecret.X else None,
          )

    default:
      raise 'Unknown command:', cmd

  Save(None)

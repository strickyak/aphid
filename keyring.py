from go import bytes, encoding/hex, fmt, io/ioutil, regexp
from go/crypto import rand, sha256
from . import conv, dh, flag, sym
from lib import data

"The global RingDict."
RingDict = {}
Ring = {}

RingFilename = flag.String('ring', '', 'name of keyring file')

RE_HEX = regexp.MustCompile('^[0-9a-f]+$').FindString
RE_BASE64 = regexp.MustCompile('^[-A-Za-z0-9_]+$').FindString

class DhKey:
  def __init__(d):
    say d
    .id = d['id']
    .pub = d['pub']
    .sec = d.get('sec')
    must RE_BASE64(.pub)
    .o_pub = dh.Big(.pub)  # big.Int
    if .sec:
      must RE_BASE64(.sec)
      .o_sec = dh.DhSecret(group=dh.GROUP, pub=.o_pub, sec=dh.Big(.sec))  # DhSecret

class SymKey:
  def __init__(d):
    .id = d['id']
    .num = d['num']
    .sym = d['sym']
    must RE_HEX(.sym)
    must len(.sym)== sym.KEY_HEX_LEN
    .b_sym = sym.DecodeHex(.sym)

class WebKey:
  def __init__(d):
    .id = d['id']
    .num = d['num']
    .xor = d['xor']
    .base = d['base']
    say .id, .xor, .base, d
    must RE_HEX(.xor)
    must len(.xor)== sym.KEY_HEX_LEN
    .b_xor = sym.DecodeHex(.xor)

class Pw:
  def __init__(d):
    .id = d['id']
    .doubleMD5 = d['doubleMD5']

def CompileDicts(d):
  """CompileDicts the dict of dicts into the dict of objects."""
  ring = {}
  say d
  for k, v in d.items():
    say k, v
    switch v['type']:
      case 'pw/doubleMD5':
        ring[k] = Pw(v)
      case 'dh':
        ring[k] = DhKey(v)
      case 'sym/aes256':
        ring[k] = SymKey(v)
      case 'web/aes256':
        ring[k] = WebKey(v)
      default:
        raise 'Unknown Type', v['type']
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
      RingDict[key_id] = dict(
          id=key_id,
          type='pw/doubleMD5',
          doubleMD5=conv.DoubleMD5(pw)
          )

    case "mkdh":
      key_id = args.pop(0)
      must not args

      obj = dh.Forge(group=dh.GROUP)
      RingDict[key_id] = dict(
          id=key_id,
          type='dh',
          pub=dh.String(obj.pub),
          sec=dh.String(obj.sec),
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
          type='sym/aes256',
          sym=conv.EncodeHex(bb),
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
          type='web/aes256',
          xor=conv.EncodeHex(xorkey),
          )

    default:
      raise 'Unknown command:', cmd

  Save(None)

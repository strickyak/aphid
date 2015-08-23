from go import bytes, encoding/hex, fmt, io/ioutil, regexp
from go/crypto import aes, rand, sha256
from . import dh, sym

"The global Ring."
Ring = {}

WRITE_PERM = 0644

RE_HEX = regexp.MustCompile('^[0-9a-f]+$').FindString
RE_BASE64 = regexp.MustCompile('^[-A-Za-z0-9_]+$').FindString

class Line:
  "Line is a single key, either aes or dh, like one line from a keyring file."
  def __init__(num=None, name=None, kind=None):
    "num, name, and kind are required."
    .num = num
    .name = name
    .kind = kind
    .pub = None
    .sec = None
    .sym = None
    .o_pub = None  # big.Int
    .o_sec = None  # DhSecret
    .b_sym = None  # byt
    .base = None

  def __repr__():
    return .__str__()
  def __str__():
    must .num
    must .name
    must .kind
    return '%s %s %s %s %s %s %s' % (
        .num if .num else '!',
        .name if .name else '!',
        .kind if .kind else '!',
        .pub if .pub else '!',
        .sec if .sec else '!',
        .sym if .sym else '!',
        .base if .base else '!')

  def SetFromWords(vec):
    must len(vec) == 7
    .num, .name, .kind, .pub, .sec, .sym, .base = vec
    .num = .num if .num != '!' else None
    .name = .name if .name != '!' else None
    .kind = .kind if .kind != '!' else None
    .pub = .pub if .pub != '!' else None
    .sec = .sec if .sec != '!' else None
    .sym = .sym if .sym != '!' else None
    .base = .base if .base != '!' else None
    must .num
    must .name
    must .kind

    if .pub:
      must type(.pub) == str
      must RE_BASE64(.pub)
      .o_pub = dh.Big(.pub)

    if .sec:
      must type(.sec) == str
      must RE_BASE64(.sec)
      .o_sec = dh.DhSecret(.num, .name, dh.GROUP, .o_pub, dh.Big(.sec))

    if .sym:
      must type(.sym) == str
      must RE_HEX(.sym)
      must len(.sym)== sym.KEY_HEX_LEN
      .b_sym = sym.DecodeHex(.sym)

    return self

def Find(k, ring):
    vec = [x for x in Ring.values() if x.num == k]
    vec += [x for x in Ring.values() if x.name == k and x.num != k]
    if len(vec) > 1:
      raise 'Too Many match key', k
    if not len(vec):
      raise 'No such key', k
    return vec[0]

def Load(fname, ring):
  "Load the ring (adding to the dict) from the file."
  for s in str(ioutil.ReadFile(fname)).split('\n'):
    s = s.strip(' \t\r')
    if not s:
      continue  # Skip blank lines.
    if s.startswith('#'):
      continue  # Skip comments.
    vec = s.split()
    must len(vec) == 7, vec
    obj = Line().SetFromWords(vec)
    ring[vec[0]] = obj  # By id.
    ring[vec[1]] = obj  # By name.

def Save(fname, ring):
  "Save the ring dict to the file."
  bb = go_new(bytes.Buffer)
  for k, v in sorted(ring.items()):
    print >>bb, str(v)
  ioutil.WriteFile(fname, bb.Bytes(), WRITE_PERM)

def main(args):
  if args:
    cmd = args.pop(0)

  say cmd, args
  switch cmd:
    case "cp":
      rfile = args.pop(0)
      wfile = args.pop(0)
      must not args
      Load(rfile, Ring)
      Save(wfile, Ring)

    case "mkdh":
      key_id = args.pop(0)
      key_name = args.pop(0)
      rfile = args.pop(0)
      wfile = args.pop(0)
      must not args
      Load(rfile, Ring)
      obj = dh.Forge(key_id, key_name, dh.GROUP)
      Ring[key_id] = Line() {
          num:key_id, name:key_name, kind:'dh',
          pub:dh.String(obj.pub), sec:dh.String(obj.sec), sym:None, base:None
      }
      Save(wfile, Ring)

    case "mksym":
      key_id = args.pop(0)
      key_name = args.pop(0)
      rfile = args.pop(0)
      wfile = args.pop(0)
      must not args
      Load(rfile, Ring)
      bb = mkbyt(32)
      c = rand.Read(bb)
      must c == 32
      obj = dh.Forge(key_id, key_name, dh.GROUP)
      Ring[key_id] = Line() {
          num:key_id, name:key_name, kind:'aes',
          pub:None, sec:None, sym:('%x'%str(bb)), base:None
      }
      Save(wfile, Ring)

    case "mkweb":
      # First use "mksym" to make the base key.
      # Then use "mkweb" to make the derived web key.
      # Do not publish the base key.
      key_id = args.pop(0)
      key_name = args.pop(0)
      key_base = args.pop(0)
      pw = args.pop(0)
      rfile = args.pop(0)
      wfile = args.pop(0)

      must not args
      Load(rfile, Ring)
      base = Find(key_base, Ring)
      basekey = base.b_sym
      say basekey

      pwhash = sha256.Sum256(pw)
      say pwhash

      webkey = basekey ^ pwhash
      say webkey

      line = Line(key_id, key_name, 'web-aes')
      line.b_sym = webkey
      line.sym = sym.EncodeHex(line.b_sym)
      line.base = key_base
      say line

      Ring[key_id] = line
      Save(wfile, Ring)

    default:
      raise 'Unknown command:', cmd


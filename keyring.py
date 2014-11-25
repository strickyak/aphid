from go import bytes, io/ioutil

"The global Ring."
Ring = {}

WRITE_PERM = 0644

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
    .base = None

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
    return self

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
    ring[vec[0]] = obj

def Save(fname, ring):
  "Save the ring dict to the file."
  bb = go_new(bytes.Buffer)
  for k, v in sorted(ring.items()):
    print >>bb, str(v)
  ioutil.WriteFile(fname, bb.Bytes(), WRITE_PERM)

def main(args):
  "main() copies one file to another, both named in args."
  rfile = args.pop(0)
  wfile = args.pop(0)

  Load(rfile, Ring)
  Save(wfile, Ring)

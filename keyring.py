from go import bytes, io/ioutil

Ring = {}

WRITE_PERM = 0644

class Line:
  def __init__(num=None, name=None, kind=None):
    .num = num
    .name = name
    .kind = kind
    .pub = None
    .sec = None
    .sym = None
    .base = None

  def String():
    must .num
    must .name
    must .kind
    return '%s %s %s %s %s %s %s' % (
        .num, .name, .kind,
        .pub if .pub else '!',
        .sec if .sec else '!',
        .sym if .sym else '!',
        .base if .base else '!')

  def SetFromWords(vec):
    must len(vec) == 7
    .num, .name, .kind, .pub, .sec, .sym, .base = vec
    .pub = .pub if .pub != '!' else None
    .sec = .sec if .sec != '!' else None
    .sym = .sym if .sym != '!' else None
    .base = .base if .base != '!' else None
    return self

def Load(fname, ring):
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
  bb = go_new(bytes.Buffer)
  for k, v in sorted(ring.items()):
    print >>bb, v.String()
  ioutil.WriteFile(fname, bb.Bytes(), WRITE_PERM)

def main(args):
  rfile = args.pop(0)
  wfile = args.pop(0)

  Load(rfile, Ring)
  Save(wfile, Ring)

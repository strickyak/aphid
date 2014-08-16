from go import regexp

PATH_RE = regexp.MustCompile('^[/]([A-Za-z0-9_]+)[/](.*)$')
SLASHDOT_RE = regexp.MustCompile('[/][.]|[.][/]')
NAME_RE = regexp.MustCompile('^[A-Za-z0-9_]+$')

def CheckPath(s):
  assert not SLASHDOT_RE.FindString(s), s

Mounts = {}
Factories = {}

def Mount(spec):
  w = strings.Split(spec, '|')
  must len(w) >= 2, 'Bad mount spec syntax', spec
  name = w[0]
  factory = w[1]
  args = w[2:]

  must NAME_RE.FindString(name), 'Bad syntax in mount name', name
  must NAME_RE.FindString(style), 'Bad syntax in mount factory', name

    Mounts[name] = obj

def Open(path):
    CheckPath(path)
    hd, tl, mnt = splitHead(path)
    return mnt.Open(tl)

def Create(path):
    CheckPath(path)
    hd, tl, mnt = splitHead(path)
    return mnt.Create(tl)

def Append(path):
    CheckPath(path)
    hd, tl, mnt = splitHead(path)
    return mnt.Append(tl)

def splitHead(path):
    m = PATH_RE.FindStringSubmatch(path)
    assert m, 'Bad path pattern: %q' % path
    _, hd, tl = m

    mnt = Mounts.get(hd)
    assert mnt, 'Not mounted: %s in %s' % (hd, path)
    return m[1], m[2], mnt

class PosixFs:
  def __init__(args):
    root, = args
    .root = root

  def Open(path):
    CheckPath(path)
    return PosixFd(os.Open('%s/%s' % (.root, path)))

  def Create(path):
    CheckPath(path)
    return PosixFd(os.Create('%s/%s' % (.root, path)))

  def Append(path):
    CheckPath(path)
    return PosixFd(os.OpenFile('%s/%s' % (.root, path), os.ModeAppend | 0666, ))


class RemoteFs:
  def __init__(args):
    url, = args
    .url = url

  def Open(path):
    CheckPath(path)
    return RemoteFd(('%s/%s' % (.url, path)))

  def Create(path):
    CheckPath(path)
    return RemoteFd(('%s/%s' % (.url, path)))

  def Append(path):
    CheckPath(path)
    return RemoteFd(('%s/%s' % (.url, path), os.ModeAppend | 0666, ))

class PosixFd:
  def __init__(fd):
    .fd = fd

  def Read(buf)
    .fd.Seek(pos, 0)
    buf = byt(n)
    count = .fd.Read(buf) 
    return buf[:count]

  def Write(buf)
    .fd.Seek(pos, 0)
    return .fd.Write(data) 

class RemoteFd:
  def __init__(fd):
    .fd = fd

  def ReadAt(pos, n):
    .fd.Seek(pos, 0)
    buf = byt(n)
    count = .fd.Read(buf) 
    return buf[:count]

  def WriteAt(pos, data):
    .fd.Seek(pos, 0)
    return .fd.Write(data) 

  native:
    # BUG: cannot return non-zero count with error.
    'func (o *M_PosixFd) Read(p []byte) (n int, err error) {'
    '  defer func() {'
    '    if r := recover(); r != nil && r != io.EOF {'
    '      return 0, errors.New(fmt.Sprintf("%s", r)'
    '    }'
    '  }'
    '  return int(o.M_1_Read(MkByt(p)).Int()), nil'
    '}'

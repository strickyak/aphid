from go import bufio, os, regexp, time
from go import io/ioutil
from go import path/filepath as F
from go import github.com/strickyak/redhed
from . import sym, table, A

DIR_PERM = 0755
FILE_PERM = 0644

Bundles = {}  # Map names to bundle.

def RevFormat(fpath, tag, ms, suffix, mtime, size):
  return '%s/%s.%014d.%s.%d.%d' % (fpath, tag, ms, suffix, mtime, size)

PARSE_REV_FILENAME = regexp.MustCompile('^r[.](\w+)[.](\w+)[.]([-0-9]+)[.]([-0-9]+)$').FindStringSubmatch

# Extracts bundle name at [2] from path to bundle.
PARSE_BUNDLE_PATH = regexp.MustCompile('(^|.*/)b[.]([A-Za-z0-9_]+)$').FindStringSubmatch

def LoadBundle(bname, topdir='.', suffix='0', keyid=None, key=None):
  if key:
    must type(key) == byt
    must len(key) == sym.KEY_BYT_LEN
  bundir = F.Join(topdir, 'b.%s' % bname)
  Bundles[bname] = Bundle(bname, bundir, suffix, keyid=keyid, key=key)

class Bundle:
  def __init__(name, bundir, suffix, keyid=None, key=None):
    .name = name
    .bundir = bundir
    .suffix = suffix
    if key:
      .key = redhed.NewKey(keyid, key)
    .table = table.Table(F.Join(.bundir, 'd.table'))
    .wikdir = F.Join(.bundir, 'd.wiki')

  def ListDirs(dirpath):
    say 'ListDirs', dirpath
    z = []
    dp = .dpath(dirpath)
    fd = os.Open(dp)
    vec = fd.Readdir(-1)
    say vec
    for info in vec:
      say info
      s = info.Name()
      if s.startswith('d.'):
        z.append(s[2:])
    say z
    return z
    
  def List2(dirpath):
    say 'List2', dirpath
    dp = .dpath(dirpath)
    fd = os.Open(dp)
    vec = fd.Readdir(-1)
    say vec
    for info in vec:
      say info
      s = info.Name()
      if s.startswith('d.'):
        yield s[2:], True
      elif s.startswith('f.'):
        yield s[2:], False
      else:
        A.Warn('Ignoring strange file: %q %q', dirpath, s)
    
  def List4(dirpath):
    say 'List4', dirpath
    dp = .dpath(dirpath)
    fd = os.Open(dp)
    vec = fd.Readdir(-1)
    say vec
    for info in vec:
      say info
      s = info.Name()
      if s.startswith('d.'):
        yield s[2:], True, -1, -1
      elif s.startswith('f.'):
        fd2 = os.Open(F.Join(dp, s))
        vec2 = fd2.Readdir(-1)
        revs = [fi.Name()
                 for fi in vec2
                 if PARSE_REV_FILENAME(fi.Name())]
        if not revs:
          continue
        rev_name = sorted(revs)[-1] # latest.
        _, name3, suffix3, mtime3, size3 = PARSE_REV_FILENAME(rev_name)
        yield s[2:], False, int(mtime3), int(size3)
      else:
        A.Warn('Ignoring strange file: %q %q', dirpath, s)
    
  def ListFiles(dirpath):
    say 'ListFiles', dirpath
    z = []
    dp = .dpath(dirpath)
    fd = os.Open(dp)
    vec = fd.Readdir(-1)
    for info in vec:
      say info, info.Name()
      s = info.Name()
      if s.startswith('f.'):
        z.append(s[2:])
    return z
    
  def ListRevs(file_path):
    z = []
    fp = .fpath(file_path)
    try:
      fd = os.Open(F.Join(.bundir, fp))
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('r.'):
        z.append(s[2:])
    return z

  def Stat3(file_path):
    dpath = .dpath(file_path)
    try:
      st = os.Stat(dpath)
      return True, -1, -1
    except:
      pass
    fpath = .fpath(file_path)
    fd = os.Open(fpath)
    names = [(fi.Name(), fi)
             for fi in fd.Readdir(-1)
             if fi.Name().startswith('r.')]
    if not names:
      raise 'No such file in bundle %s: %q' % (.name, file_path)

    _, latest_fi = names[-1]
    assert not latest_fi.IsDir()
    return False, latest_fi.ModTime(), latest_fi.Size()

  def dpath(dirpath):
    vec = [str(s) for s in dirpath.split('/') if s]
    z = F.Join(.bundir, *['d.%s' % s for s in vec])
    say dirpath, z
    return z

  def fpath(file_path):
    say file_path
    vec = [str(s) for s in file_path.split('/') if s]
    fname = vec.pop()
    dp = .dpath('/'.join(vec))
    z = F.Join(dp, 'f.%s' % fname)
    say file_path, z
    return z

  def ReadFile(file_path):
    if .key:
      fd = os.Open(.nameOfFileToOpen(file_path))
      with defer fd.Close():
        r = redhed.NewReader(fd, .key)
        return ioutil.ReadAll(r)
    else:
      return ioutil.ReadFile(.nameOfFileToOpen(file_path))

  def WriteFile(file_path, s, mtime=-1):
    say 'WriteFile', file_path, len(s)
    mtime = mtime if mtime>0 else time.Now().Unix()
    w = atomicFileCreator(.fpath(file_path), .suffix, mtime=mtime, size=len(s))
    with defer w.Close():
      if .key:
        ww = w
        w = redhed.NewWriter(ww, .key, file_path, mtime)

      try:
        if type(s) is str:
          w.WriteString(s)  # Fully.
        else:
          w.Write(byt(s))  # Fully.
      except as ex:
        w.Abort()
        raise ex

      if ww:
        w.Close()

  def nameOfFileToOpen(file_path):
    fp = .fpath(file_path)
    gg = sorted([str(f) for f in F.Glob(F.Join(fp, 'r.*'))])
    if not gg:
      raise 'no such file: bundle=%s path=%s' % (.name, file_path)
    z = gg[-1]  # The latest one is last, in sorted order.
    say file_path, z
    return z

  def Open(file_path):
    return os.Open(.nameOfFileToOpen(file_path))

class atomicFileCreator:
  def __init__(fpath, suffix, mtime, size):
    .fpath = fpath
    .suffix = suffix
    .mtime = mtime
    .size = size

    ms = NowMillis()
    if not .mtime:
      .mtime = ms // 1000
    .tmp = RevFormat(.fpath, 'tmp', ms, .suffix, .mtime, .size)
    say 'os.Create', .tmp
    os.MkdirAll(.fpath, DIR_PERM)
    .fd = os.Create(.tmp)
    .bw = bufio.NewWriter(.fd)

  def Flush():
    return .bw.Flush()
  def Write(bb):
    say 'Write', len(bb)
    return .bw.Write(bb)  # bufio writes fully, or error.
  def WriteByte(b):
    say 'WriteByte', b
    .bw.WriteByte(b)
  def WriteString(s):
    say 'WriteString', len(s)
    return .bw.WriteString(s)

  def Abort():
    try:
      say 'ABORTING ============='
      .fd.Close()
    except:
      pass
    say 'Abort: os.Remove', .tmp
    os.Remove(.tmp)
    .bw = None
    .fd = None

  def Close():
    say 'CLOSING ============='
    .bw.Flush()
    .fd.Close()

    ms = NowMillis()
    dest = RevFormat(.fpath, 'r', ms, .suffix, .mtime, .size)

    say 'os.Rename', .tmp, dest
    os.Rename(.tmp, dest)

native:
  'func (self *C_atomicFileCreator) WriteAt(p []byte, off int64) (n int, err error) {' 
  '  _ = off'
  '  bb := MkByt(p)'
  '  self.M_1_Write(bb)'
  '  return  len(p), nil'
  '}'

  'func (self *C_atomicFileCreator) Write(p []byte) (n int, err error) {'
  '  bb := MkByt(p)'
  '  self.M_1_Write(bb)'
  '  return  len(p), nil'
  '}'

def NowMillis():
    return time.Now().UnixNano() // 1000000

pass

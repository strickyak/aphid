from go import bufio, os, regexp, sync, time
from go import io/ioutil
from go import path/filepath as F
from go import crypto/md5, crypto/sha256
from go import github.com/strickyak/redhed
from . import  A, pubsub, sym, table

DIR_PERM = 0755
FILE_PERM = 0644

# TODO: Get rid of this global.
###Bundles = {}  # Map names to bundle.

def TailGlob(pattern):
  for x in F.Glob(pattern):
    yield F.Base(x)

def TRY(fn):
  try:
    fn()
  except:
    pass

def NowMillis():
    return time.Now().UnixNano() // 1000000

def RevFormat(fpath, tag, ms, suffix, mtime, size, rhkey):
  if rhkey:
    xname = redhed.EncryptFilename('%014d.%s.%d.%d' % (ms, suffix, mtime, size), rhkey)
    return '%s/%s^%s' % (fpath, tag, xname)
  else:
    return '%s/%s.%014d.%s.%d.%d' % (fpath, tag, ms, suffix, mtime, size)

PARSE_REV_FILENAME = regexp.MustCompile('^r[.](\w+)[.](\w+)[.]([-0-9]+)[.]([-0-9]+)$').FindStringSubmatch

# Extracts bundle name at [2] from path to bundle.
PARSE_BUNDLE_PATH = regexp.MustCompile('(^|.*/)b[.]([A-Za-z0-9_]+)$').FindStringSubmatch

class AttachedWebkeyBundle:
  def __init__(aphid, bname, topdir='.', suffix, webkeyid, webkey, basekey):
    .aphid = aphid
    must webkeyid
    must webkey
    must type(webkey) == byt
    must len(webkey) == 32  # 256 bit.
    .bname, .topdir, .suffix = bname, topdir, suffix
    .webkeyid, .webkey, .basekey = webkeyid, webkey, basekey
    .links = 0
    .mu = go_new(sync.Mutex)
    .wx = True  # Does use encrypted webpw -- please Link(pw) it.
    .bundir = F.Join(topdir, 'b.%s' % bname)


  def SymKeyFromWebPw(pw):
    # TODO -- extract from multi-pw
    h = sha256.Sum256(pw.strip(' \t\n\r'))
    must len(h) == 32 # 256 bits.
    return h ^ .webkey  # In rye, xor of byt & byt is byt.

  def Link(pw):
    .mu.Lock()
    with defer .mu.Unlock():
      if .links == 0:
        symkey = .SymKeyFromWebPw(pw)
        .bund = Bundle(.aphid, .bname, .bundir, .suffix, keyid=.basekey, key=symkey)
      .links += 1

  def Unlink():
    .mu.Lock()
    with defer .mu.Unlock():
      .links -= 1
      if not .links:
        .bund = None

  def Stat3(path):
    must .links
    return .bund.Stat3(path)
  def List4(path):
    must .links
    return .bund.List4(path)
  def ReadFile(path, rev=None):
    must .links
    return .bund.ReadFile(path, rev)
  def WriteFile(path, data, mtime=-1, rev=None, slave=None):
    must .links
    return .bund.WriteFile(path, data, mtime, rev, slave)

  def ListDirs(path):
    return [name for name, isDir, _, _ in .List4(path) if isDir]
  def ListFiles(path):
    return [name for name, isDir, _, _ in .List4(path) if not isDir]


class Bundle:
  def __init__(aphid, bname, bundir, suffix, keyid=None, key=None):
    .aphid = aphid
    .bus = aphid.bus
    say bname, bundir, suffix, keyid, key
    .bname = bname
    .bundir = bundir
    .suffix = suffix
    if key:
      must type(key) == byt
      must len(key) == sym.KEY_BYT_LEN
      .rhkey = redhed.NewKey(keyid, key)
      say .rhkey
    .table = table.Table(F.Join(.bundir, 'd.table'))
    .wikdir = F.Join(.bundir, 'd.wiki')
    .wx = False  # Does not use encrypted webpw

  # These are NOPs in a regular bundle.
  def Link(pw):
    pass
  def Unlink():
    pass

  def ListDirs(path):
    say 'ListDirs', path
    z = []
    dp = .dpath(path)
    fd = os.Open(.bpath(dp))
    vec = fd.Readdir(-1)
    say vec
    for info in vec:
      say info
      s = info.Name()
      if s.startswith('d.'):
        z.append(s[2:])
    say z
    return z

  def List4(path):
    say 'List4', path
    dp = .dpath(path)
    try:
      fd = os.Open(.bpath(dp))
      vec = fd.Readdir(-1)
    except:
      return  # from Generator.
    say vec
    for info in vec:
      say info
      s = info.Name()
      if s.startswith('d.'):
        yield s[2:], True, -1, -1
      elif s.startswith('d^'):
        yield redhed.DecryptFilename(s[2:], .rhkey), True, -1, -1
      elif s.startswith('f.'):
        fd2 = os.Open(.bpath(F.Join(dp, s)))
        vec2 = fd2.Readdir(-1)
        revs = [fi.Name()
                 for fi in vec2
                 if PARSE_REV_FILENAME(fi.Name())]
        if not revs:
          continue
        rev_name = sorted(revs)[-1] # latest.
        _, name3, suffix3, mtime3, size3 = PARSE_REV_FILENAME(rev_name)
        yield s[2:], False, int(mtime3), int(size3)
      elif s.startswith('f^'):
        fname2 = redhed.DecryptFilename(s[2:], .rhkey)
        fd2 = os.Open(.bpath(F.Join(dp, s)))
        vec2 = fd2.Readdir(-1)
        say fname2, fd2, vec2

        xrevs = [fi.Name() for fi in vec2 if fi.Name().startswith('r^')]
        revs = ['r.' + redhed.DecryptFilename(x[2:], .rhkey) for x in xrevs]

        if not revs:
          continue
        rev_name = sorted(revs)[-1] # latest.
        _, name3, suffix3, mtime3, size3 = PARSE_REV_FILENAME(rev_name)
        yield fname2, False, int(mtime3), int(size3)
      else:
        A.Warn('Ignoring strange file: %q %q', path, s)

  def ListFiles(path):
    say 'ListFiles', path
    z = []
    dp = .dpath(path)
    fd = os.Open(.bpath(dp))
    vec = fd.Readdir(-1)
    for info in vec:
      say info, info.Name()
      s = info.Name()
      if s.startswith('f.'):
        z.append(s[2:])
      if s.startswith('f^'):
        z.append(redhed.DecryptFilename(s[2:], .rhkey))
    return z

  def ListRevs(path):
    z = []
    fp = .fpath(path)
    try:
      fd = os.Open(.bpath(fp))
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('r.'):
        z.append(s[2:])
      if s.startswith('r^'):
        z.append(redhed.DecryptFilename(s[2:], .rhkey))
    return z

  def Stat3(path):
    dpath = .dpath(path)
    try:
      st = os.Stat(.bpath(dpath))
      return True, -1, -1
    except:
      pass

    fpath = .fpath(path)
    fd = os.Open(.bpath(fpath))
    rev, filename = .nameOfFileToOpen(path)
    say rev, filename

    m = PARSE_REV_FILENAME(rev)
    must m, (m, rev, filename)
    _, ts, suffix, mtime, size = m
    return False, time.Unix(int(mtime), 0), int(size)

  def findOrConjure(xdir, s, prefix):
    say xdir, s, prefix
    try:
      fd = os.Open(.bpath(xdir))
    except:
      pass
    if fd:
      for fi in fd.Readdir(-1):
        name = fi.Name()
        if len(name) > 15 and name.startswith(prefix):
          plainname = redhed.DecryptFilename(name[2:], .rhkey)
          say s, name, plainname
          if plainname == s:
            return name
    z = redhed.EncryptFilename(s, .rhkey)
    say s, z
    return '%s%s' % (prefix, z)

  def bpath(path):
    return F.Join(.bundir, path)

  def dpath(path):
    say path
    vec = [str(s) for s in path.split('/') if s]
    say vec

    if .rhkey:
      xdir = '.'
      say xdir
      for s in vec:
        say s
        xpart = .findOrConjure(xdir, s, 'd^')
        xdir = F.Join(xdir, xpart)
      return xdir
    else:
      return F.Join('.', *['d.%s' % s for s in vec])

  def fpath(path):
    say path
    vec = [str(s) for s in path.split('/') if s]

    fname = vec.pop()
    dp = .dpath('/'.join(vec))
    say path, dp
    if .rhkey:
      xdir = dp
      xpart = .findOrConjure(xdir, s, 'f^')
      xfile = F.Join(xdir, xpart)
      say path, xfile
      return xfile
    else:
      z = F.Join(dp, 'f.%s' % fname)
      say path, z
      return z

  def NewReadSeekerTimeSize(path, rev=None):
    say path, rev
    if .rhkey:
      rev, xname = .nameOfFileToOpen(path, rev)
      say xname
      fd = os.Open(.bpath(xname))
      rs = redhed.NewReader(fd, .rhkey)
      mtime, size, _ = rs.TimeSizeHash()
      return rs, mtime, size
      # TODO -- how will we Close?
    else:
      rev, name = .nameOfFileToOpen(path, rev)
      say name
      words = name.split('/')[-1].split('.')
      mtime, size = int(words[2]), int(words[3])
      say mtime, size, words, name
      return os.Open(.bpath(name)), mtime, size

  def ReadFile(path, rev=None):
    say path, rev
    if .rhkey:
      rev, xname = .nameOfFileToOpen(path, rev)
      say xname
      fd = os.Open(.bpath(xname))
      with defer TRY(lambda: fd.Close()):
        r = redhed.NewReader(fd, .rhkey)
        z = ioutil.ReadAll(r)
        say len(z), z[:80]
        TRY(lambda: r.Close())
        return z
    else:
      rev, name = .nameOfFileToOpen(path, rev)
      say name
      z = ioutil.ReadFile(.bpath(name))
      say len(z), z[:80]
      return z

  def ReadRawFile(rawpath):
    fullpath = F.Join(.bundir, rawpath)
    say rawpath, fullpath
    z = ioutil.ReadFile(fullpath)
    say len(z), z[:80]
    return z

  def WriteRawFile(rawpath, data):
    must type(data) == byt
    say rawpath, len(data)
    w = atomicFileCreator(self, rawpath)
    try:
      w.Write(data)  # Fully.
      w.Close()
    except as ex:
      w.Abort()
      raise ex

  def WriteFile(path, data, mtime=-1, rev=None, slave=None):
    bb = byt(data)
    mtime = mtime if mtime>0 else time.Now().Unix()
    say 'WriteFile', path, len(bb), mtime, rev
    say 'WriteFile2', .bname, .bundir, .suffix, .rhkey
    w = atomicFileRevCreator(self, .fpath(path), .suffix, mtime=mtime, size=len(bb), rev=rev, rhkey=.rhkey)

    try:
      if .rhkey:
        csum = md5.Sum(bb)
        say 'redhed.NewWriter', path, mtime, len(bb), csum
        redw = redhed.NewWriter(w, .rhkey, path, mtime, len(bb), csum)
        say redw
        writer = redw
      else:
        writer = w

      try:
        writer.Write(bb)  # Fully.
      except as ex:
        if .rhkey:
          redw.Abort()
        raise ex

      if .rhkey:
        redw.Close()
    except as ex:
      w.Abort()
      raise ex
    rawpath = w.Close()

    if not slave:
      t = pubsub.Thing(origin=None, key1='WriteRawFile', key2=.bname, props=dict(rawpath=rawpath))
      .bus.Publish(t)

  def nameOfFileToOpen(path, rev=None):
    """Returns rev, raw"""
    say path
    fp = .fpath(path)
    say fp
    if rev:
      # TODO -- we need plain vs. z, in case of .rhkey.
      return F.Join(fp, rev), .bpath(F.Join(fp, rev))
    if .rhkey:
      baseglob = TailGlob(F.Join(fp, 'r^*'))
      say baseglob
      pairs = sorted([('r.' + redhed.DecryptFilename(x[2:], .rhkey), x) for x in baseglob])
      say pairs
    else:
      tails = sorted([str(f) for f in TailGlob(F.Join(.bpath(fp), 'r.*'))])
      raws = [F.Join(fp, g) for g in tails]
    say raws
    if not raws:
      raise 'no such file: bundle=%s path=%s' % (.bname, path)
    if .rhkey:
      raw = F.Join(.bpath(fp), raws[-1][1])  # raw r^* filename is the second in the tuple
      rev = pairs[-1][0]
    else:
      rev = tails[-1]
      raw = raws[-1]  # The latest one is last, in sorted order.
    say path, rev, raw
    return rev, raw

class atomicFileCreator:
  def __init__(bund, dest):
    say bund, dest
    .bund = bund
    .dest = dest
    d = F.Dir(.dest)
    b = F.Base(.dest)

    .tmp = F.Join(d, 'tmp.' + b)
    say 'os.Create', .tmp
    os.MkdirAll(.bund.bpath(d), DIR_PERM)
    .fd = os.Create(.bund.bpath(.tmp))
    .bw = bufio.NewWriter(.fd)

  def Flush():
    return .bw.Flush()
  def Write(bb):
    say 'Write', len(bb)
    return .bw.Write(bb)  # bufio writes fully, or error.
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
    os.Remove(.bund.bpath(.tmp))
    .bw = None
    .fd = None

  def Close():
    say 'CLOSING ============='
    .bw.Flush()
    .fd.Close()

    say 'os.Rename', .tmp, .dest, 'RELATIVE TO', .bund.bpath('.')
    os.Rename(.bund.bpath(.tmp), .bund.bpath(.dest))
    return .dest

class atomicFileRevCreator(atomicFileCreator):
  def __init__(bund, fpath, suffix, mtime, size, rev, rhkey):
    .bund = bund
    .fpath = fpath
    .suffix = suffix
    .mtime = mtime
    .size = size
    .rhkey = rhkey
    .rev = rev

    ms = NowMillis()
    if not .mtime:
      .mtime = ms // 1000

    if .rev:
      dest = '%s/%s' % (.fpath, .rev)
    else:
      ms = NowMillis()
      dest = RevFormat(.fpath, 'r', ms, .suffix, .mtime, .size, .rhkey)

    super.__init__(bund, dest)

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

pass

from go import bufio, bytes, io, log, os, regexp, strings, sync, time
from go import io/ioutil, encoding/hex
from go import path as P
from go import path/filepath as F
from go import crypto/sha256, crypto/rand
from go import github.com/strickyak/redhed
from . import  A, pubsub, sym, table
from . import  resize
from lib import sema

DIR_PERM = 0755
FILE_PERM = 0644

TheSerial = sema.Serial()

def ReadFile(bund, path, pw=None, raw=None, rev=None, varient='r'):
  r, rev_out = bund.MakeReaderAndRev(path, pw=pw, raw=raw, rev=rev, varient=varient)
  say bund, path, rev, rev_out
  w = go_new(bytes.Buffer)
  io.Copy(w, r)
  r.Close()
  return w.String()

def WriteFile(bund, path, body, pw=None, mtime=0, raw=None, varient='r', suffix=''):
  if not mtime:
    mtime = NowMillis()
  say 'FRODO WriteFile', bund, path, len(body), pw, raw, mtime, varient, suffix
  r = ioutil.NopCloser(bytes.NewReader(byt(body)))
  w = bund.MakeWriter(path, pw=None, mtime=mtime, raw=None, varient=varient, suffix=suffix)
  io.Copy(w, r)
  say bund, path, len(body), pw
  w.Close()
  r.Close()

  #if not raw and varient == 'r':
  #  try:
  #    resize.MakeThumbnails(bund, path, body, pw, mtime, WriteFile)
  #  except as ex:
  #    say ex

def ListDirs(b, d, pw=None):
  return list([x for x, isDir, _, _ in b.List4(d, pw) if isDir])

def ListFiles(b, d, pw=None):
  return list([x for x, isDir, _, sz in b.List4(d, pw) if not isDir and sz])

def osTailGlob(pattern):
  for x in TRY(lambda: F.Glob(pattern)):
    yield F.Base(x)

def TRY(fn):
  try:
    z = fn()
    #say z
    return z
  except as ex:
    say ex
    return None

def NowMillis():
    return time.Now().UnixNano() // 1000000

PARSE_REV_FILENAME = regexp.MustCompile('^(r|v[a-z0-9_]+)[.](\w+)[.](\w+)[.]([-0-9]+)[.]([-0-9]+)(.*)$').FindStringSubmatch

V_DOT = regexp.MustCompile('^v_([0-9]+)_([0-9]+)_([a-z]+)[.](.*)$').FindStringSubmatch
V_HAT = regexp.MustCompile('^(v[a-z0-9_]+)\\^(.*)$').FindStringSubmatch

# Extracts bundle name at [2] from path to bundle.
PARSE_BUNDLE_PATH = regexp.MustCompile('(^|.*/)b[.]([A-Za-z0-9_]+)$').FindStringSubmatch

class Base:
  def __init__():
    .wx = None  # Tested by awiki.
  def CanThumbnail():
    return True
  def OsReadDir(s):
    fd = os.Open(F.Join(.bundir, s))
    with defer fd.Close():
      return fd.Readdir(-1)
  def TryOsReadDir(s):
    say s
    z = TRY(lambda: .OsReadDir(s))
    say z
    return z

  def Link(pw):
    pass
  def Unlink():
    pass

  def ListDirs(d, pw=None):
    return [x for x, isdir, _, _ in .List4(d, pw) if isdir]
  def ListFiles(d, pw=None):
    return [x for x, isdir, _, sz in .List4(d, pw) if not isdir and sz]

  def MakeWriter(path, pw=None, mtime=0, raw=None, varient='r', suffix=''):
    say 'FRODO CALL .MakeChunkWriter', path, pw, mtime, raw, varient, suffix
    z = .MakeChunkWriter(path, pw=pw, mtime=mtime, raw=raw, varient=varient, suffix=suffix)
    say 'FRODO CALLED .MakeChunkWriter', path, pw, mtime, raw, varient, suffix
    return z

  def __str__():
    return '%T{%s}' % (self, .bname)
  def __repr__():
    return '%T{%s}' % (self, .bname)

class WebkeyBundle(Base):
  def __init__(aphid, bname, topdir='.', suffix, webkeyid, xorkey, basekey):
    .aphid = aphid
    must webkeyid
    must xorkey
    must type(xorkey) == byt
    must len(xorkey) == sym.KEY_BYT_LEN  # 256 bit.
    .bname, .topdir, .suffix = bname, topdir, suffix
    .webkeyid, .xorkey, .basekey = webkeyid, xorkey, basekey
    .links = 0
    .mu = go_new(sync.Mutex)
    .wx = True  # Does use encrypted webpw -- please Link(pw) it.
    .bundir = F.Join(topdir, 'b.%s' % bname)

  def SymKeyFromWebPw(pw):
    # TODO -- extract from multi-pw
    h = sha256.Sum256(pw.strip(' \t\n\r'))
    must len(h) == 32 # 256 bits.
    return h ^ .xorkey  # In rye, xor of byt & byt is byt.

  def Link(pw):
    must pw
    .mu.Lock()
    with defer .mu.Unlock():
      symkey = .SymKeyFromWebPw(pw)
      if .links == 0:
        .bund = RedhedBundle(.aphid, .bname, .bundir, .suffix, keyid=.basekey, key=symkey)
      else:
        # Don't allow different key
        must .bund.symkey == symkey
      .links += 1

  def UnlinkIfPw(pw):
    if pw:
      .Unlink()
  def Unlink():
    .mu.Lock()
    with defer .mu.Unlock():
      .links -= 1
      if not .links:
        .bund = None

  def MakeReaderAndRev(path, pw, raw, rev=None, varient='r'):
    must pw or raw
    say path, pw, raw
    if pw:
      .Link(pw)
    must .links or raw
    with defer .UnlinkIfPw(pw):
      return .bund.MakeReaderAndRev(path, pw=pw, raw=raw, rev=rev, varient=varient)

  def MakeChunkReader(path, pw=None, raw=False, varient='r'):
    must pw or raw
    say path, pw, raw

    if raw:
      fd = os.Open(F.Join(.bundir, path))
      return ChunkReaderAdapter(fd)

    if pw:
      .Link(pw)
    must .links or raw
    with defer .UnlinkIfPw(pw):
      return .bund.MakeChunkReader(path, pw=pw, raw=raw, varient=varient)

  def MakeChunkWriter(path, pw, mtime, raw, varient='r', suffix=''):
    must pw or raw
    say path, pw
    if pw:
      .Link(pw)
    must .links or raw
    with defer .UnlinkIfPw(pw):
      return .bund.MakeChunkWriter(path, pw=pw, mtime=mtime, raw=raw, varient=varient, suffix=suffix)

  def Stat3(path, pw=None, varient='r', nodir=False):
    must pw
    if pw:
      .Link(pw)
    must .links
    with defer .UnlinkIfPw(pw):
      return .bund.Stat3(path, varient=varient, nodir=nodir)
  def List4(path, pw=None, varient='r'):
    must pw
    if pw:
      .Link(pw)
    must .links
    with defer .UnlinkIfPw(pw):
      return .bund.List4(path, varient=varient)

  def ReadRawFile(rawpath):
    dont_use_key = None
    b = PlainBundle(.aphid, .bname, .bundir, .suffix, keyid=dont_use_key, key=dont_use_key)
    return b.ReadRawFile(rawpath)
  def WriteRawFile(rawpath, data):
    dont_use_key = None
    b = PlainBundle(.aphid, .bname, .bundir, .suffix, keyid=dont_use_key, key=dont_use_key)
    return b.WriteRawFile(rawpath, data)


class PlainBundle(Base):
  def __init__(aphid, bname, bundir, suffix, keyid=None, key=None):
    say bname, bundir, suffix, keyid, key
    .aphid = aphid
    .bus = aphid.bus if .aphid else None
    .bname = bname
    .bundir = bundir
    .suffix = suffix
    must not key
    .table = table.Table(F.Join(.bundir, 'd.table'))
    os.MkdirAll(bundir, 0777)

  def List4(path, pw=None, varient='r'):
    say 'List4', path
    dp = .dpath(path)
    vec = .TryOsReadDir(dp)
    for info in vec:
      say info
      s = info.Name()
      if s.startswith('d.'):
        say s[2:], True, -1, -1
        yield s[2:], True, -1, -1
      elif s.startswith('f.'):
        fd2 = os.Open(.bpath(F.Join(dp, s)))
        vec2 = fd2.Readdir(-1)
        revs = [fi.Name()
                 for fi in vec2
                 if PARSE_REV_FILENAME(fi.Name())]
        if not revs:
          continue
        rev_name = sorted(revs)[-1] # latest.
        _, varient3, name3, suffix3, mtime3, size3, more = PARSE_REV_FILENAME(rev_name)
        say s[2:], False, int(mtime3), int(size3)
        yield s[2:], False, int(mtime3), int(size3)
      else:
        log.Printf('Ignoring strange file: %q %q', path, s)

  def ListRevs(path, varient='r'):
    z = []
    fp = .fpath(path)
    try:
      say 'ListRevs Open', path, fp, varient
      fd = os.Open(.bpath(fp))
    except as ex:
      say 'ListRevs except', path, fp, ex
      return z
    vec = fd.Readdir(-1)
    say 'ListRevs vec', path, fp, vec, varient
    for info in vec:
      s = info.Name()
      say 'ListRevs info', path, fp, s
      if varient=='r':
        if s.startswith('r.'):
          z.append(s)
        elif s.startswith('r^'):
          z.append(redhed.DecryptFilename(s[2:], .rhkey))
        else:
          say 'Ignore', s
      else:
        raise varient  # TODO -- varient obsolete here.
      say 'ListRevs append', path, len(z), z[-1] if z else None
    say 'ListRevs return', z
    return z


  def ListImageVarients(path, rev=None):
    fp = .fpath(path)
    try:
      say 'ListImageVarients Open', path, fp
      fd = os.Open(.bpath(fp))
    except as ex:
      say 'ListImageVarients except', path, fp, ex
      return None
    vec = fd.Readdir(-1)
    say 'ListImageVarients vec', path, fp, vec

    if not rev:
      z = []
      for info in vec:
        s = info.Name()
        say 'ListImageVarients info', path, fp, s
        if s.startswith('r.'):
          z.append(s)
        elif s.startswith('r^'):
          z.append(redhed.DecryptFilename(s[2:], .rhkey))
        else:
          say 'Ignore', s
      rev = sorted(z)[-1]

    z = []
    for info in vec:
      s = info.Name()
      say 'ListImageVarients CONSIDER', s
      m = V_DOT(s)
      if m:
        _, wid, hei, kind, tail = m
        if tail != rev[2:]:
          say 'ListImageVarients CONTINUE', s, tail, rev
          continue
        z.append((s, int(wid), int(hei)))
        say 'ListImageVarients APPEND', s, int(wid), int(hei)
      elif V_HAT(s):
        x = redhed.DecryptFilename(s[2:], .rhkey)
        m = V_DOT(x)
        if m:
          _, wid, hei, kind, tail = m
          if tail != rev: continue
          z.append(redhed.DecryptFilename(s[2:], .rhkey))
          z.append((s, int(wid), int(hei)))
        else:
          raise x
      else:
        say 'Ignore', s
      say 'ListImageVarients append', path, len(z), z[-1] if z else None
    say 'ListImageVarients return', z
    return z

  def Stat3(path, pw=None, rev=None, varient='r', nodir=False):
    if not nodir:
      try:
        # First try it as a directory.
        st = os.Stat(.bpath(.dpath(path)))
        return True, -1, -1  # IsDir, mtime -1, length -1.
      except:
        pass

    fpath = .fpath(path)
    fd = os.Open(.bpath(fpath))
    rev2, filename = .nameOfFileToOpen(path, rev=rev, varient=varient)
    say rev2, filename

    m = PARSE_REV_FILENAME(F.Base(filename))
    must m, (m, rev, rev2, filename)
    _, varient3, ts, suffix, millis, size, more = m
    return False, int(millis), int(size)

  def bpath(path):
    return F.Join(.bundir, path)

  def dpath(path):
    say path
    vec = [str(s) for s in path.split('/') if s]
    say vec
    return F.Join('.', *['d.%s' % s for s in vec])

  def fpath(path):
    say path
    vec = [str(s) for s in path.split('/') if s]

    fname = vec.pop()
    dp = .dpath('/'.join(vec))
    say path, dp
    z = F.Join(dp, 'f.%s' % fname)
    say path, z
    return z

  def NewReadSeekerTimeSize(path, rev=None, varient='r'):
    say path, rev
    rev, name = .nameOfFileToOpen(path, rev=rev, varient=varient)
    say name
    words = name.split('/')[-1].split('.')
    mtime, size = int(words[3]), int(words[4])
    say mtime, size, words, name
    return os.Open(name), mtime, size

  def nameOfFileToOpen(path, rev=None, varient='r'):
    """Returns rev, raw"""
    say .bundir, .bname, path
    fp = .fpath(path)
    say .bundir, .bname, fp
    if rev:
      # TODO -- we need plain vs. z, in case of .rhkey.
      return F.Join(fp, rev), .bpath(F.Join(fp, rev))
    tails = sorted([str(f) for f in osTailGlob(F.Join(.bpath(fp), '%s.*' % varient))])
    raws = [F.Join(.bpath(fp), g) for g in tails]

    if not raws:
      raise 'no such file: bundle=%s path=%s' % (.bname, path)

    rev = tails[-1]
    raw = raws[-1]  # The latest one is last, in sorted order.
    say path, rev, raw
    return rev, raw

  def MakeReaderAndRev(path, pw, raw, rev=None, varient='r'):
    # Raw doesn't matter, on a Plain Bundle file.
    must not pw
    say path, raw, rev
    if raw:
      say (.bundir, path)
      return os.Open(F.Join(.bundir, path)), None
    else:
      rev, filename = .nameOfFileToOpen(path=path, rev=rev, varient=varient)
      say rev, filename, (path, rev)
      return os.Open(filename), rev

  def MakeChunkReader(path, pw, raw=False, rev=None, varient='r'):
    r, rev_out = .MakeReaderAndRev(path=path, pw=pw, raw=raw, rev=rev, varient=varient)
    say path, rev, rev_out, varient
    return ChunkReaderAdapter(r)

  def MakeChunkWriter(path, pw, mtime, raw, varient='r', suffix=''):
    must not pw
    say path, pw
    cw = ChunkWriter(self, None, path, mtime, raw, varient=varient, suffix=suffix)
    say str(cw)
    return cw

class RedhedBundle(Base):
  def __init__(aphid, bname, bundir, suffix, keyid=None, key=None):
    .aphid = aphid
    .bus = aphid.bus if aphid else None
    say bname, bundir, suffix, keyid, key
    .bname = bname
    .bundir = bundir
    .suffix = suffix
    must key
    must type(key) == byt
    must len(key) == sym.KEY_BYT_LEN
    .rhkey = redhed.NewKey(keyid, key)
    say .rhkey
    #.table = table.Table(F.Join(.bundir, 'd.table'))
    os.MkdirAll(bundir, 0777)

  def CanThumbnail():
    return False  # TODO -- fix RedhedBundle for thumbnails.
  def OsReadDir(s):
    fd = os.Open(F.Join(.bundir, s))
    with defer fd.Close():
      return fd.Readdir(-1)
  def TryOsReadDir(s):
    say s
    z = TRY(lambda: .OsReadDir(s))
    say z
    return z

  def List4(path, pw=None, varient='r'):
    say 'List4', path
    dp = .dpath(path)
    vec = .TryOsReadDir(dp)
    for info in vec:
      say info
      x = info.Name()
      s = redhed.DecryptFilename(x, .rhkey)

      if s.startswith('d.'):
        yield s[2:], True, -1, -1

      elif s.startswith('f.'):
        fd2 = os.Open(.bpath(F.Join(dp, x)))
        vec2 = fd2.Readdir(-1)
        say s, x, fd2, vec2

        xrevs = [fi.Name() for fi in vec2 if fi.Name().startswith('%') and len(fi.Name()) > 40]
        revs = []
        for x in xrevs:
          rev = redhed.DecryptFilename(x, .rhkey)
          if rev.startswith('%s.' % varient):
            revs.append(rev)
        if revs:
          rev_name = sorted(revs)[-1] # latest.
          m = PARSE_REV_FILENAME(rev_name)
          if not m:
            raise 'Cannot PARSE_REV_FILENAME: ' + repr((rev_name, dp, s))
          _, varient3, name3, suffix3, millis, size3, more = m
          yield s[2:], False, int(millis), int(size3)
      else:
        log.Printf('Ignoring strange file: %q %q', path, s)

  def ListRevs(path, varient='r'):
    z = []
    fp = .fpath(path)
    try:
      fd = os.Open(.bpath(fp))
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('%') and len(s) > 40:
        z.append(redhed.DecryptFilename(s, .rhkey))
    return sorted(z)

  def Stat3(path, pw=None, rev=None, varient='r', nodir=False):
    dpath = .dpath(path)
    say path, dpath, pw
    if not nodir:
      try:
        say .bpath(dpath)
        st = os.Stat(.bpath(dpath))
        return True, -1, -1
      except:
        pass

    say path, dpath, pw
    rev, filename = .nameOfFileToOpen(path, varient='r', rev=rev)
    say rev, filename

    m = PARSE_REV_FILENAME(rev)
    must m, (m, rev, filename)
    _, varient3, ts, suffix, millis, size, more = m
    return False, int(millis), int(size)

  def findOrConjure(xdir, s):
    return redhed.GetEncryptedPath(xdir, s, .rhkey)

    say xdir, s
    try:
      say .bpath(xdir)
      fd = os.Open(.bpath(xdir))
    except as ex:
      say 'Could not open', ex
      pass
    if fd:
      for fi in fd.Readdir(-1):
        name = fi.Name()
        if len(name) > 40 and name.startswith('%'):
          plainname = redhed.DecryptFilename(name, .rhkey)
          say s, name, plainname
          if plainname == s:
            say 'return', name
            return name
    z = redhed.EncryptFilename(s, .rhkey)
    say s, z
    return z

  def bpath(path):
    return F.Join(.bundir, path)

  def dpath(path):
    say path
    vec = [str(s) for s in path.split('/') if s and s != "."]
    say vec

    top = .bundir
    say top
    xpath = ''
    for s in vec:
      dpart = 'd.%s' % s
      say "zyx", top, xpath, dpart
      xpart = .findOrConjure(top, dpart)
      top = F.Join(top, xpart)
      xpath = F.Join(xpath, xpart) if xpath else xpart
    say "zyxxx", xpath
    return xpath

  def fpath(path):
    say path
    dp = .dpath(F.Dir(path))
    fname = F.Base(path)
    fpart = 'f.%s' % fname
    xpart = .findOrConjure(F.Join(.bundir, dp), fpart)
    z = F.Join(dp, xpart)
    say "zyxfff", path, dp, fname, fpart, xpart, z
    return z

  def NewReadSeekerTimeSize(path, rev=None, varient='r'):
    say path, rev
    if .rhkey:
      rev, xname = .nameOfFileToOpen(path, rev=rev, varient=varient)
      say xname
      fd = os.Open(.bpath(xname))
      rs = redhed.NewReader(fd, .rhkey)
      mtime, size, _ = rs.TimeSizeHash()
      return rs, mtime, size
      # TODO -- how will we Close?
    else:
      rev, name = .nameOfFileToOpen(path, rev=rev, varient=varient)
      say name
      words = name.split('/')[-1].split('.')
      mtime, size = int(words[2]), int(words[3])
      say mtime, size, words, name
      return os.Open(.bpath(name)), mtime, size

  def nameOfFileToOpen(path, rev=None, varient='r'):
    """Returns rev, raw"""
    say path
    fp = .fpath(path)
    say fp
    if rev:
      # TODO -- we need plain vs. z, in case of .rhkey.
      return F.Join(fp, rev), .bpath(F.Join(fp, rev))

    must .rhkey
    say (F.Join(.bundir, fp, '%*'))
    raws = list(osTailGlob(F.Join(.bundir, fp, '%*')))
    say raws
    pairs = sorted([(redhed.DecryptFilename(x, .rhkey), x) for x in raws])
    say pairs

    say raws
    if not raws:
      raise 'no such file: bundle=%s path=%s' % (.bname, path)

    raw = F.Join(.bpath(fp), pairs[-1][1])  # raw r^* filename is the second in the tuple
    say raw, 0
    rev = pairs[-1][0]
    say rev, 0

    say path, rev, raw
    return rev, raw

  def MakeReaderAndRev(path, pw, raw, rev=None, varient='r'):
    if raw:
      assert not pw
      assert not rev
      return os.Open(F.Join(.bundir, path)), None

    say path, raw, rev
    rev, filename = .nameOfFileToOpen(path=path, rev=rev, varient=varient)
    fd = os.Open(filename)
    return redhed.NewReader(fd, .rhkey), rev

  def MakeChunkReader(path, pw, raw=False, rev=None, varient='r'):
    r, _ = .MakeReaderAndRev(path=path, pw=pw, raw=raw, rev=rev, varient=varient)
    return ChunkReaderAdapter(r)

  def MakeChunkWriter(path, pw, mtime, raw, varient='r', suffix=''):
    say path, pw
    z = ChunkWriter(self, .rhkey, path, mtime, raw, varient=varient, suffix=suffix)
    say z
    return z

class ChunkWriterAdapter:
  def __init__(w):
    .w = w

  def WriteChunk(buf):
    c = .w.Write(byt(buf))
    say len(buf), c
    return c

  def Close():
    say 'Close', .w
    if .w:
      say .w
      .w.Close()
      .w = None

  def Dispose():
    say 'Dispose', .w
    if .w:
      say .w
      .w.Close()
      .w = None

class ChunkReaderAdapter:
  def __init__(r):
    .r = r

  def ReadChunk(n):
    say n
    bb = .SafeReadChunk(n)
    say n, len(bb)
    return bb

  def Close():
    say 'Close'
    if .r:
      try:
        .r.Close()
        .r = None
      except:
        pass
  def Dispose():
    say 'Dispose'
    if .r:
      try:
        .r.Close()
        .r = None
      except:
        pass

  def SafeReadChunk(n):
    native:
      `
         r := self.M_r.Contents().(i_io.Reader)
         n := a_n.Int()
         bb := make([]byte, int(n))
         cc, err := r.Read(bb)
         if err == nil {
           return MkByt(bb[:cc])
         }
         if err == io.EOF {
           return MkByt(bb[:cc])
         }
         panic(err)
      `

class chunkReader:
  def __init__(bund, rhkey, path, raw, varient='r'):
    if raw:
      .fd = os.Open(F.Join(bund.bundir, path))
      .r = bufio.NewReader(.fd)
    else:
      say bund, rhkey, path
      rev1, path1 = bund.nameOfFileToOpen(path, varient=varient)
      say path1
      path2 = F.Join(bund.bundir, path1)
      say path2
      .fd = os.Open(path2)
      if rhkey:
        .r = redhed.NewReader(.fd, rhkey)
      else:
        .r = .fd
      say .fd, .r

  def ReadChunk(n):
    say n
    bb = mkbyt(n)
    c = .r.Read(bb)
    say c, n
    return bb[:c]

  def Close():
    say 'Close'
    .fd.Close()
    .fd = None
  def Dispose():
    say 'Dispose'
    if .fd:
      .fd.Close()
    .fd = None

class RawChunkWriter:
  def __init__(bund, path, mtime):
    say bund, path, mtime
    .bund = bund
    .path = path
    .mtime = mtime
    junk = mkbyt(10)
    rand.Read(junk)
    hexjunk = hex.EncodeToString(junk)
    .tmppath = F.Join(.bund.bundir, 'tmp.%s' % hexjunk)
    os.MkdirAll(.bund.bundir, 0777)
    .fd = os.Create(.tmppath)
    .w = bufio.NewWriter(.fd)
  def WriteChunk(bb):
    c = .w.Write(bb)
    must c == len(bb)
  def Close():
    .w.Flush()
    .fd.Close()
    target = F.Join(.bund.bundir, .path)
    os.MkdirAll(F.Dir(target), 0777)
    os.Rename(.tmppath, target)
    if .mtime:
      t = time.Unix(0, .mtime * 1000000)  # Nano to Millis
    else:
      t = time.Now()
    os.Chtimes(target, time.Now(), t)
native:
  `
    func (self *C_RawChunkWriter) Write(p []byte) (n int, err error) {
      return self.M_w.Contents().(io.Writer).Write(p)
    }
  `

class ChunkWriter:
  def __init__(bund, rhkey, path, mtime, raw, varient='r', suffix=''):
    path = P.Clean(P.Join('.', path))
    say path, mtime, raw
    must not strings.HasPrefix(path, '%')
    .bund = bund
    .rhkey = rhkey
    .path = path
    .mtime = mtime
    .raw = raw
    .varient = varient
    .suffix = suffix
    if .raw:
      say 'FRODO RAW', type(bund), bund.bname, bund.bundir, rhkey, path, mtime, raw, varient, suffix
      .tmp = F.Join(.bund.bundir, 'tmp.ChunkWriter.%d' % TheSerial.Recv())
      os.MkdirAll(F.Dir(.tmp), 0777)
      .fd = os.Create(.tmp)
      .w = bufio.NewWriter(.fd)
    else:
      say 'FRODO COOKED', type(bund), bund.bname, bund.bundir, rhkey, path, mtime, raw, varient, suffix
      assert varient == 'r' or suffix
      .fd = None
      .w = redhed.NewStreamWriter(.bund.bundir, rhkey, redhed.Magic2, mtime, .fnGetName)

  def WriteChunk(bb):
    while bb:
      c = .w.Write(bb)
      must c > 0
      bb = bb[c:]

  def Close():
    if .raw:
      .w.Flush()
      .fd.Close()

      target = F.Join(.bund.bundir, .path)
      os.MkdirAll(F.Dir(target), 0777)
      os.Rename(.tmp, target)
      .RawDest = .path
    else:
      .w.Close()
      .RawDest = .w.RawDest
    say .raw, .path, .RawDest
    must .RawDest

    .w = None
    .fd = None
    .Publish()

    if .bund.CanThumbnail() and not .raw and .varient == 'r':
      say 'FRODO CW CALL resize.MakeThumbnailsNoBody', .path, .revpath, .revnow, .varient, .suffix
      try:
        # TODO -- pw=None? get pw from where?
        resize.MakeThumbnailsNoBody(.bund, .path, pw=None, rev=.revnow, suffix=.revpath, writeFileFn=WriteFile, readFileFn=ReadFile)
      except as ex:
        say 'FRODO CW CATCH resize.MakeThumbnailsNoBody', ex

  def Publish():
    if not .raw:
      t = pubsub.Thing(origin=None, key1='WriteFile', key2=.bund.bname, props=dict(rawpath=.RawDest, DEBUG_path=.path))
      if .bund.bus:
        .bund.bus.Publish(t)

  def Dispose():
    say 'Dispose'
    if .fd:
      .fd.Close()
    .fd = None
    if .w:
      .w.Close()
    .w = None

  def fnGetName(w):
    try:
      vec = .path.split('/')
      f = vec.pop()
      dpath = F.Join(F.Join(*[('d.%s' % x) for x in vec]), 'f.%s' % f)
      if .suffix:
        .revpath = '%s%s' % (.varient, .suffix[1:])
      else:
        .revnow = int(time.Now().UnixNano() / 1000000)  # timestamp is now, even if mtime is old,
        .revmtime = w.MTimeMillis
        .revsize = w.Size
        .revhash = hex.EncodeToString(w.Hash[:9])
        .revpath = '%s.%014d._.%d.%d.%s' % (.varient, .revnow, .revmtime, .revsize, .revhash)
        say .revnow, .revmtime, .revsize, .revhash, .revpath
      path = P.Join(dpath, .revpath)
    except as ex:
      raise ex
    return path

native:
  `
    func (self *C_ChunkWriter) Write(p []byte) (n int, err error) {
      return self.M_w.Contents().(io.Writer).Write(p)
    }
  `

def CopyChunks(w, r):
  say str(w), str(r)
  try:
    while True:
      x = r.ReadChunk(256*256)
      say len(x)
      if not x:
        return
      w.WriteChunk(x)
  except as ex:
    say ex
    must strings.Contains(ex, 'EOF'), ex

def RawFileExits(bund, path):
  fullpath = F.Join(bund.bundir, path)
  basename = F.Base(fullpath)
  try:
    fd = os.Open(basename)
    must fd
  except:
    return False

  # If we can parse the basename, check file length.
  m3 = PARSE_REV_FILENAME(basename)
  if m3:
    _, varient3, name3, suffix3, mtime3, size3, more3 = m3
    size = int(size3)
    if size >= 0:
      try:
        info = fd.Stat()
        must info
      except:
        return False
      if info.IsDir():
        return False
      if size != info.Size():
        return False
  return True  # Assume all is OK if we cannot check more.

pass

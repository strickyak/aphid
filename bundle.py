from go import bufio
from go import io/ioutil
from go import os
from go import path/filepath as F
from go import regexp
from go import time
from . import table

DIR_PERM = 0755
FILE_PERM = 0644

Bundles = {}  # Map names to bundle.

PARSE_BUNDLE_PATH = regexp.MustCompile('(^|.*/)b[.]([A-Za-z0-9_]+)$').FindStringSubmatch

def LoadBundles(topdir='.', suffix='0'):
  vec = F.Glob(F.Join(topdir, 'b.*'))
  if not vec:
    raise 'No bundles in top directory', topdir
  for d in vec:
    say d
    m = PARSE_BUNDLE_PATH(d)
    say m
    if m:
      _, _, bname = m
      say bname
      Bundles[bname] = Bundle(bname, d, suffix)

class Bundle:
  def __init__(name, bundir, suffix):
    .name = name
    .bundir = bundir
    .suffix = suffix
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
    
  def ListFiles(dirpath):
    say 'ListFiles', dirpath
    z = []
    dp = .dpath(dirpath)
    say dp
    #try:
    fd = os.Open(dp)
    say fd
    #except:
    #  return z
    vec = fd.Readdir(-1)
    say vec
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

  def dpath(dirpath):
    say dirpath
    vec = [str(s) for s in dirpath.split('/') if s]
    say vec
    z = F.Join(.bundir, *['d.%s' % s for s in vec])
    say "dpath -> ", z
    return z

  def fpath(file_path):
    say file_path
    vec = [str(s) for s in file_path.split('/') if s]
    say vec
    fname = vec.pop()
    say fname
    dp = .dpath('/'.join(vec))
    say dp
    z = F.Join(dp, 'f.%s' % fname)
    say "fpath -> ", z
    return z

  def ReadFile(file_path):
    return ioutil.ReadFile(.nameOfFileToOpen(file_path))

  def WriteFile(file_path, s):
    # TODO: use fileCreator.
    ioutil.WriteFile(.nameOfFileToCreate(file_path), s, FILE_PERM)

  def nameOfFileToOpen(file_path):
    say file_path
    fp = .fpath(file_path)
    say fp
    gg = sorted([str(f) for f in F.Glob(F.Join(fp, 'r.*'))])
    say gg
    if not gg:
      raise 'no such file: bundle=%s path=%s' % (.name, file_path)
    z = gg[-1]  # The latest one is last, in sorted order.
    say 'nameOfFileToOpen', z
    return z

  def nameOfFileToCreate(file_path):
    say file_path
    fp = .fpath(file_path)
    say fp
    ms = NowMillis()
    z = '%s/r.%d.%s' % (fp, ms, .suffix)
    say 'nameOfFileToCreate', z
    return z

  def Open(file_path):
    return os.Open(.nameOfFileToOpen(file_path))

  def Create(file_path):
    fp = .fpath(file_path)
    os.MkdirAll(fp, DIR_PERM)
    raise 'TODO'

# TODO: Try this fileCreator, for atomic creates.
class fileCreator:
  def __init__(fpath, suffix):
    .fpath = fpath
    .suffix = suffix
    ms = NowMillis()
    .tmp = 'tmp.%014d.%s' % (ms, .suffix)
    .fd = os.Create(.tmp)
    .bw = bufio.NewWriter(.fd)

  def Write(bb):
    return .bw.Write(bb)
  def WriteByte(b):
    .bw.Write(b)
  def WriteString(s):
    return .bw.WriteString(s)

  def Close():
    .bw.Flush()
    .fd.Close()

    ms = NowMillis()
    dest = 'r.%014d.%s' % (ms, .suffix)

    os.Rename(.tmp, dest)

def NowMillis():
    now = time.Now()
    sec, ns = now.Unix(), now.UnixNano()
    return sec*1000 + ns // 1000000

pass

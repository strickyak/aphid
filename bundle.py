from go import bufio
from go import os
from go import path/filepath as F
from go import regexp
from go import time
from . import table

DIR_PERM = 7*7*7 + 5*7 + 5 # Octal 0755

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
    z = []
    dp = .dpath(dirpath)
    try:
      fd = os.Open(dp)
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('d.'):
        z.append(s[2:])
    return z
    
  def ListFiles(dirpath):
    z = []
    dp = .dpath(dirpath)
    try:
      fd = os.Open(dp)
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
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

  def Open(file_path):
    say file_path
    fp = .fpath(file_path)
    say fp
    gg = sorted([str(f) for f in F.Glob(F.Join(fp, 'r.*'))])
    say gg
    if not gg:
      raise 'no such file', .name, file_path
    return os.Open(gg[-1])  # The latest one is last, in sorted order.

  def Create(file_path):
    fp = .fpath(file_path)
    os.MkdirAll(fp, DIR_PERM)
    raise 'TODO'


class fileCreator:
  def __init__(fpath, suffix):
    .fpath = fpath
    .suffix = suffix
    now = time.Now()
    sec, ns = now.Unix(), now.UnixNano()
    ms = sec*1000 + ns // 1000000
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

    now = time.Now()
    sec, ns = now.Unix(), now.UnixNano()
    ms = sec*1000 + ns // 1000000
    dest = 'r.%014d.%s' % (ms, .suffix)

    os.Rename(.tmp, dest)

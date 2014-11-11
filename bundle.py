from go import bufio
from go import os
from go import path/filepath
from go import time
from . import table

J = filepath.Join

DIR_PERM = 7*7*7 + 5*7 + 5 # Octal 0755

class Bundle:
  def __init__(name, bundir, suffix):
    .name = name
    .bundir = bundir
    .suffix = suffix
    .table = table.Table(J(.bundir, 'd.table'))
    .wikdir = J(.bundir, 'd.wiki')

  def ListDirs(dirpath):
    z = []
    dpath = .dpath(dirpath)
    try:
      fd = os.Open(J(.bundir, dpath))
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('d.'):
        z.append(s)
    return z
    
  def ListFiles(dirpath):
    z = []
    dpath = .dpath(dirpath)
    try:
      fd = os.Open(J(.bundir, dpath))
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('f.'):
        z.append(s)
    return z
    
  def ListRevs(file_path):
    z = []
    fpath = .fpath(file_path)
    try:
      fd = os.Open(J(.bundir, fpath))
    except:
      return z
    vec = fd.Readdir(-1)
    for info in vec:
      s = info.Name()
      if s.startswith('r.'):
        z.append(s)
    return z

  def dpath(dirpath):
    vec = [str(s) for s in filepath.SplitList(dirpath)]
    return J(.bundir, *['d.%s' % s for s in vec])

  def fpath(file_path):
    vec = [str(s) for s in filepath.SplitList(file_path)]
    fname = vec.pop()
    dpath = J(*['d.%s' % s for s in vec])
    return J(.bundir, dpath, 'f.%s' % fname)

  def Open(file_path):
    fpath = .fpath(file_path)
    gg = sorted([str(f) for f in filepath.Glob(J(fpath, 'r.*'))])
    if not gg:
      raise 'no such file', .name, file_path
    return os.Open(gg[-1])  # The latest one is last, in sorted order.

  def Create(file_path):
    fpath = .fpath(file_path)
    os.MkdirAll(fpath, DIR_PERM)


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

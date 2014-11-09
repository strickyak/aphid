from go import os
from go import path as P
from go import regexp
from go import time

from go import github.com/strickyak/aphid

from . import rfs

HEAD_TAIL = regexp.MustCompile('^[/]*([A-Za-z0-9_:.]+)([/]+(.*))?$')
DOUBLE_DOT = regexp.MustCompile('[.][.]')
OCTAL700 = 7 * 64

def Clean(path):
  "Clean and check DOUBLE_DOT."
  path = P.Clean(path)
  must not DOUBLE_DOT.FindString(path), repr(path)
  return path

Factories = { 'Here': HereFs(), 'There': ThereFs(), 'Std': StdFs(), }

def splitHeadTail(path):
    path = Clean(path)
    m = HEAD_TAIL.FindStringSubmatch(path)
    must m, 'Bad path pattern: %q' % path
    _, hd, _, tl = m
    return hd, P.Clean(tl)

def splitFactory(path):
    hd, tl = splitHeadTail(path)
    fact = Factories.get(hd)
    must fact, 'No Such Factory: %q in path %q' % (hd, path)
    return fact, tl

def Open(path):
    path = Clean(path)
    fact, tl = splitFactory(path)
    return fact.Open(tl)

def Create(path):
    path = Clean(path)
    fact, tl = splitFactory(path)
    return fact.Create(tl)

def Append(path):
    path = Clean(path)
    fact, tl = splitFactory(path)
    return fact.Append(tl)

def List(path):
    path = Clean(path)
    fact, tl = splitFactory(path)
    for a,b,c,d in fact.List(tl):
      yield Clean('/%s/%s' % (fact, a)),b,c,d

def SetModTime(path, secs):
    path = Clean(path)
    fact, tl = splitFactory(path)
    fact.SetModTime(tl, secs)

class StdFs:
  def __init__():
    pass

  def Open(path):
    must path == 'in'
    return HereFd(os.Stdin)

  def Create(path):
    must path == 'out'
    return HereFd(os.Stdout)

  def Append(path):
    must path == 'out'
    return HereFd(os.Stdout)

class HereFs:
  def __init__():
    pass

  def Open(path):
    return HereFd(os.Open(P.Join('.', path)))

  def Create(path):
    os.MkdirAll(P.Dir(P.Join('.', path)), OCTAL700)
    return HereFd(os.Create(P.Join('.', path)))

  def Append(path):
    return HereFd(os.OpenFile(P.Join('.', path), os.ModeAppend | 0666, ))

  def SetModTime(path, secs):
    mtime = time.Unix(secs, 0)
    os.Chtimes(P.Join('.', path), mtime, mtime)

class HereFd:
  def __init__(fd):
    .fd = fd

  def ModTime():
    st = .fd.Stat()
    return st.ModTime().Unix()

  def Read(n):
    z = aphid.WrapRead(.fd, n)
    return z

  def Write(data):
    z = aphid.WrapWrite(.fd, data) 
    return z

  def List():
    for info in .fd.Readdir(-1):
      yield info.Name(), info.IsDir(), info.ModTime().Unix(), info.Size()

  def Close():
    .fd.Close()

class ThereFs:
  def __init__():
    pass

  def Open(path):
    return ThereFd(path, 'r')

  def Create(path):
    return ThereFd(path, 'w')

  def Append(path):
    return ThereFd(path, 'a')

class ThereFd:
  def __init__(path, mode):
    path = P.Clean(path)
    m = HEAD_TAIL.FindStringSubmatch(path)
    must m, 'Bad path pattern: %q' % path
    _, where, _, tl = m
    .cli = rfs.RfsClient(where, rfs.KEYNAME, rfs.KEY)
    .path = tl
    .pos = 0

  def Read(n):
    buf, eof = .cli.AReadAt(.path, n, .pos) 
    .pos += len(buf)
    return buf, eof

  def Write(data):
    count = .cli.AWriteAt(.path, data, .pos) 
    .pos += count
    return count

  def ReadAt(n, pos):
    .pos = pos
    buf, eof = .Read(n)
    return buf, eof

  def WriteAt(data, pos):
    .pos = pos
    return .Write(data)

  def List():
    return .cli.AListDir(.path)

  def Close():
    pass

pass

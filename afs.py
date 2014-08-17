from go import os
from go import regexp
from go import github.com/strickyak/aphid

from . import rfs

PATH_HEAD_TAIL_RE = regexp.MustCompile('^[/]*([A-Za-z0-9_:.]+)[/]+(.*)$')
SLASHDOT_RE = regexp.MustCompile('[/][.]|[.][/]')

def CheckPath(s):
  must not SLASHDOT_RE.FindString(s), s

Factories = { 'Here': HereFs(), 'There': ThereFs(), }

def separateFactory(path):
    m = PATH_HEAD_TAIL_RE.FindStringSubmatch(path)
    must m, 'Bad path pattern: %q' % path
    _, hd, tl = m

    fact = Factories.get(hd)
    must fact, 'No Factory: %s in %s' % (hd, path)
    return m[1], m[2], fact

def Open(path):
    CheckPath(path)
    hd, tl, fact = separateFactory(path)
    return fact.Open(tl)

def Create(path):
    CheckPath(path)
    hd, tl, fact = separateFactory(path)
    return fact.Create(tl)

def Append(path):
    CheckPath(path)
    hd, tl, fact = separateFactory(path)
    return fact.Append(tl)

class HereFs:
  def __init__():
    pass

  def Open(path):
    CheckPath(path)
    return HereFd(os.Open('./%s' % path))

  def Create(path):
    CheckPath(path)
    return HereFd(os.Create('./%s' % path))

  def Append(path):
    CheckPath(path)
    return HereFd(os.OpenFile('./%s' % path, os.ModeAppend | 0666, ))


class HereFd:
  def __init__(fd):
    .fd = fd

  def Read(n):
    return aphid.WrapRead(.fd, n)

  def Write(data):
    return aphid.WrapWrite(.fd, data) 

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
    CheckPath(path)
    m = PATH_HEAD_TAIL_RE.FindStringSubmatch(path)
    must m, 'Bad path pattern: %q' % path
    _, where, tl = m
    .cli = rfs.Client(where)
    .path = tl
    .pos = 0

  def Read(n):
    say 'YYY enter cli AReadAt'
    buf, eof = .cli.AReadAt(.path, n, .pos) 
    say 'YYY leave cli AReadAt', len(buf), buf, eof
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

  def Close():
    pass

pass

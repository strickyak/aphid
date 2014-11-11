from go import bufio
from go import os
from go import path/filepath
from . import skiplist

class Table:
  def __init__(dirpath):
    .dirpath = dirpath
    .ts = None
    .w = None
    .d = skiplist.SkipList()
    .loadDir()

  def loadDir():
    glob = filepath.Glob(filepath.Join(.dirpath,'t.*'))
    for g in glob if glob else []:
      .slurpFile(g)

  def slurpFile(filename):
    hold = []
    for line in ReadFileLines(filename):
      if line.startswith(';'):
        .addem(hold)
        hold = []
      elif line.startswith('+'):
        vec = line.split()
        if len(vec) == 3:
          hold.append(vec)
        elif len(vec) == 2:
          vec.append(False)
          hold.append(vec)
        
  def addem(hold):
    for ts, k, v in hold:
      if v:
        .d[k] = (ts, v)
        .d.Set(k, (ts, v))
      else:
        .d.Remove(k)




def ReadFileLines(filename):
  r = os.Open(filename)
  with defer r.Close():
    sc = bufio.NewScanner(r)
    while sc.Scan():
      yield sc.Text()
    sc.Err() # Raise error, if any.

def WriteFileLines(filename, it):
  fd = os.Create(filename)
  with defer fd.Close():
    bw = bufio.NewWriter(fd)
    with defer bw.Flush():
      for line in it:
        bw.WriteString(line)
        bw.WriteByte('\n')

class LineFileWriter:
  def __init__(filename):
    .fd = os.Create(filename)
    .bw = bufio.NewWriter(.fd)
  def WriteString(s):
    .bw.WriteString(s)
    .bw.WriteByte('\n')
  def Flush():
    .bw.Flush()
  def Close():
    .bw.Flush()
    .fd.Close()

pass

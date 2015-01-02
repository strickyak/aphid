from go import bufio
from go import os
from go import path/filepath
from . import skiplist

class Table:
  # Construct with dirpath where the t.* files are, and they will be loaded.
  def __init__(dirpath):
    .dirpath = dirpath
    .ts = None
    .w = None
    .d = skiplist.SkipList()
    .loadDir()

  def loadDir():
    for g in filepath.Glob(filepath.Join(.dirpath,'t.*')):
      .slurpFile(g)

  def slurpFile(filename):
    hold = []
    for line in ReadFileLines(filename):
      if line.startswith(';'):
        # Semicolon lines commit the hold.
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
      # Look for ts of existing record with key k.
      # Remember that ts are strings, not numbers.
      p = .d.Get(k)
      t = p[0] if p else ''
      if ts >= t:
        if v:
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

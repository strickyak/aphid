from go import bufio, fmt, os, time
from go import path/filepath as F
from . import skiplist

class Table:
  # Construct with dpath where the t.* files are, and they will be loaded.
  def __init__(dpath, suffix='0'):
    .dpath = dpath
    .suffix = suffix
    .sk = skiplist.SkipList()
    .loadDir()

  def Stamp():
    return '%d.%s' % (time.Now().Unix() // 1000000, .suffix)

  def PrepareToWrite():
    if not .w:
      filename = F.Join(.dpath, 't.%s' % .Stamp())
      .fd = os.Create(filename)
      .w = bufio.NewWriter(.fd)

  def ItemsWithPrefix(prefix):
    it = .sk.Items(prefix)
    for k, (ts, val) in it:
      if k.startswith(prefix):
        yield k, val
      else:
        return

  def Get(k):
    rec = .sk.Get(k)
    if rec:
      ts, val = rec
      return val
    else:
      return None

  def Set(k, v):
    .PrepareToWrite()
    ts = .Stamp()
    .sk.Set(k, (ts, v))
    if v is None:
      print >>.w, '-%s\t%s\n' % (ts, k)
    else:
      print >>.w, '+%s\t%s\t%s\n' % (ts, k, v)
    print >>.w, ';\n'
    .w.Flush()

  def loadDir():
    for g in F.Glob(F.Join(.dpath,'t.*')):
      .slurpFile(g)

  def slurpFile(filename):
    pending = []
    for line in ReadFileLines(filename):
      if line.startswith(';'):
        # Semicolon lines commit the pending records.
        .addem(pending)
        pending = []
      elif line.startswith('+'):
        vec = line.split('\t')
        must len(vec) == 3
        pending.append(vec)
      elif line.startswith('-'):
        vec = line.split('\t')
        must len(vec) == 2
        vec.append(None)  # Add None as third thing.
        pending.append(vec)
        
  def addem(hold):
    for ts, k, v in hold:
      ts = ts.lstrip('+-')  # Omit the '+' or '-'.

      # Look for ts of existing record with key k.
      # Remember that ts are strings, not numbers.
      rec = .sk.Get(k)
      old_ts = rec[0] if rec else ''
      if ts >= old_ts:
        .sk.Set(k, (ts, v))

def ReadFileLines(filename):
  r = os.Open(filename)
  with defer r.Close():
    sc = bufio.NewScanner(r)
    while sc.Scan():
      yield sc.Text()
    sc.Err() # Raise error, if any.

class LineFileWriter:
  def __init__(filename):
    .fd = os.Create(filename)
    .w = bufio.NewWriter(.fd)
  def Printf(*args):
    fmt.Fprintf(.w, *args)
  def Flush():
    .w.Flush()
  def Close():
    .w.Flush()
    .fd.Close()
  #def WriteString(s):
  #  .w.WriteString(s)
  #  .w.WriteByte('\n')

#def WriteFileLines(filename, it):
#  fd = os.Create(filename)
#  with defer fd.Close():
#    bw = bufio.NewWriter(fd)
#    with defer bw.Flush():
#      for line in it:
#        bw.WriteString(line)
#        bw.WriteByte('\n')

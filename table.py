from go import bufio, fmt, os, time
from go import path.filepath as F
import A, skiplist
from "github.com/strickyak/rye/contrib" import data

class Table:
  # Construct with dpath where the t.* files are, and they will be loaded.
  def __init__(dpath, suffix='0'):
    .dpath = dpath
    .suffix = suffix
    .sk = skiplist.SkipList()
    .loadDir()

  def Stamp():
    return '%d.%s' % (A.NowMillis(), .suffix)

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

  def Put(k, v):
    .PrepareToWrite()
    ts = .Stamp()
    .sk.Put(k, (ts, v))
    if v is None:
      print >>.w, '-%s\t%s' % (ts, k)
    else:
      print >>.w, '+%s\t%s\t%s' % (ts, k, v)
    print >>.w, ';'
    .w.Flush()

  def loadDir():
    for g in F.Glob(F.Join(.dpath,'t.*')):
      .slurpFile(g)

  def slurpFile(filename):
    pending = []
    for line in ReadFileLines(filename):
      if line.startswith(';'):
        # Commit the pending records.
        .addem(pending)
        pending = []
      elif line.startswith('+'):
        # Make an Insert record.
        vec = line.split('\t')
        say vec
        must len(vec) == 3
        pending.append(vec)
      elif line.startswith('-'):
        # Make an Drop record.
        vec = line.split('\t')
        must len(vec) == 2
        vec.append(None)  # Add None as third thing.
        pending.append(vec)
        
  def addem(pending):
    for ts, k, v in pending:
      ts = ts.lstrip('+-')  # Omit the '+' or '-'.

      # Look for ts of existing record with key k.
      # Remember that ts are strings, not numbers.
      rec = .sk.Get(k)
      old_ts = rec[0] if rec else ''
      if ts >= old_ts:
        .sk.Put(k, (ts, v))

def ReadFileLines(filename):
  r = os.Open(filename)
  with defer r.Close():
    sc = bufio.NewScanner(r)
    while sc.Scan():
      yield sc.Text()
    sc.Err() # Raise error, if any.

#Encode = conv.EncodeCurlyWeak
#Decoee = conv.DecodeCurly 

class Fields:
  def __init__(table, indexed_fields):
    .table = table
    .indexed_fields = indexed_fields

  def Get(bname, fname, key):
    k = '%s!%s!%s' % (bname, fname, key)
    vv = .table.Get(k)
    return data.Eval(vv)

  def Put(bname, fname, key, val):
    k = '%s!%s!%s' % (bname, fname, key)
    .table.Put(k, repr(val))

  pass # TODO

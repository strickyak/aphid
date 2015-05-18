from go import bufio, io/ioutil, os
from go import path/filepath as F
from go import github.com/strickyak/redhed
from . import bundle, keyring

Ring = {}
keyring.Load('test.ring', Ring)
must Ring.get('YAK')
must Ring.get('BLM')
must Ring.get('WLM')

REV1 =  'r.01000111222333.test.01000111222999.6'
T1 = 1000111222999
T2 = 1000333222999

class FakeBus:
  def __init__():
    pass
  def Publish(x):
    pass
FB = FakeBus()
class FakeAphid:
  def __init__():
    .bus = FB
FA = FakeAphid()

def ArgsKw(*args, **kw):
  return args, kw

def TestBundles():
  bundir = F.Join(TD, 'b.plain')
  say bundir
  os.MkdirAll(F.Join(bundir, 'd.d1/d.d2/f.file1'), 0777)
  ioutil.WriteFile(F.Join(bundir, 'd.d1/d.d2/f.file1', REV1),
                   'bilbo\n', 0666)

  say '############################################################################'
  b = bundle.PlainBundle(FA, 'plain', bundir, 'PP', keyid=None, key=None)
  say '############################################################################'
  Do1Bundle(b)
  say '############################################################################'

  bundir = F.Join(TD, 'b.red')
  pw = Ring['YAK'].b_sym
  key = redhed.NewKey('YAK', pw)
  say bundir, pw, key
  d1x = redhed.EncryptFilename('d.d1', key)
  d2x = redhed.EncryptFilename('d.d2', key)
  file1x = redhed.EncryptFilename('f.file1', key)
  revx = redhed.EncryptFilename(REV1, key)

  say F.Join(bundir, d1x, d2x, file1x)
  os.MkdirAll(F.Join(bundir, d1x, d2x, file1x), 0777)

  def namer(w):
    must w.Size == 6
    #say F.Join(bundir, d1x, d2x, file1x, revx)
    #return F.Join(bundir, d1x, d2x, file1x, revx)
    say    F.Join('d.d1', 'd.d2', 'f.file1', REV1)
    return F.Join('d.d1', 'd.d2', 'f.file1', REV1)
  w = redhed.NewStreamWriter(bundir, key, redhed.Magic2, T1, namer)
  say w
  bw = bufio.NewWriter(w)
  bw.Write(byt('bilbo\n'))
  bw.Flush()
  w.Close()

  say '############################################################################'
  b = bundle.RedhedBundle(FA, 'red', bundir, 'RR', keyid='YAK', key=Ring['YAK'].b_sym)
  say '############################################################################'
  Do1Bundle(b)
  say '############################################################################'

def Do1Bundle(b):
  say b
  isDir, millis, size = b.Stat3('d1/d2')
  say isDir, millis, size
  must (isDir, millis, size) == (True, -1, -1)

  isDir, millis, size = b.Stat3('d1/d2/file1')
  say isDir, millis, size
  must (isDir, millis, size) == (False, T1, 6)

  vec = list(b.List4('/'))
  say vec
  must vec == [("d1", True, -1, -1)]

  vec = list(b.List4('/d1'))
  say vec
  must vec == [("d2", True, -1, -1)]

  vec = list(b.List4('/d1/d2'))
  say vec
  must vec == [("file1", False, T1, 6)]

  r = b.MakeReader('/d1/d2/file1', None, None)
  say r
  d6 = ioutil.ReadAll(r)
  say d6
  must d6 == byt('bilbo\n')
  r.Close()

  cr = b.MakeChunkReader('/d1/d2/file1', None, None)
  say cr
  d6 = cr.ReadChunk(99)
  say d6
  must d6 == byt('bilbo\n')
  cr.Close()

  cw = b.MakeChunkWriter(path='/d1/d2/file1', pw=None, mtime=T2, raw=None)
  cw.WriteChunk('samwise\n')
  cw.Close()

  vec = list(b.List4('/d1/d2'))
  say vec
  must vec == [("file1", False, T2, 8)]

  r = b.MakeReader('/d1/d2/file1', None, None)
  d8 = ioutil.ReadAll(r)
  r.Close()
  must d8 == byt('samwise\n')

TD = ioutil.TempDir('', 'tmp.bundle_test.')
if 1: # with defer os.RemoveAll(TD):
  TestBundles()
print >> os.Stderr,  'OKAY bundle_test.py'

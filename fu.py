from go import os

#from go import github.com/strickyak/aphid

from . import flag
from . import afs
from . import rfs

def Test1(args):
  fs = rfs.Client('localhost:9876')

  vec = fs.ListDir('vga')
  say 'ListDir', vec
  assert len(vec) > 2
  assert len(vec[1]) == 4

  buf, eof = fs.ReadAt('motd', 8, 0)
  say 'ReadAt', buf, eof
  assert len(buf) == 8
  assert not eof

  buf, eof = fs.ReadAt('motd', 12, 8)
  say 'ReadAt', buf, eof
  assert len(buf) == 12
  assert not eof

  print "OK"

BS = 512 # Block Size

def cat1(filepath, out):
  fd = afs.Open(filepath)
  say 'YYY cat1', fd
  defer fd.Close()
  while True:
    say 'YYY cat1 fd.Read', fd
    buf, eof = fd.Read(BS)
    say 'YYY cat1 fd.Read', buf, eof
    if buf:
      ### aphid.WrapWrite(out, buf)  # Writes fully.
      n = len(buf)
      while n > 0:
        c = out.Write(buf)
        buf = buf[c:]
        n -= c
        say 'YYYYYYYY', n, c
    say 'YYY called aphid.WrapWrite', len(buf), buf
    if eof:
      break
  pass

def Cat(args):
  out = None
  if CREATE:
    must not APPEND
    out = afs.Create(CREATE)
    defer out.Close()
  if APPEND:
    must not CREATE
    out = afs.Append(APPEND)
    defer out.Close()
  if not out:
    out = afs.Append('/Std/out')
  for arg in args:
    cat1(arg, out)
  pass

Ensemble = { 'test1': Test1, 'cat': Cat, }

CREATE = flag.String('create', '', 'Create output file with "cat" command.')
APPEND = flag.String('append', '', 'Append output file with "cat" command.')

def main(args):
  global CREATE, APPEND
  args = flag.Take(args)
  #CREATE = str(goreify(goderef(CREATE)))
  #APPEND = str(goreify(goderef(APPEND)))
  CREATE = CREATE()
  APPEND = APPEND()
  say CREATE, APPEND
  say type(CREATE), type(APPEND)
  say len(CREATE), len(APPEND)
  say False or CREATE, False or APPEND

  if not len(args):
    say 'Expected an Emsemble argument:', [k for k in Ensemble]
    os.Exit(13)

  cmd, args = args[0], args[1:]
  f = Ensemble.get(cmd)
  if not f:
    say "No such command:", cmd
    os.Exit(11)

  f(args)

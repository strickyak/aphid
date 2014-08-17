from go import os

from go import github.com/strickyak/aphid

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

BS = 4096 # Block Size

def cat1(filepath):
  fd = afs.Open(filepath)
  say 'YYY cat1', fd
  defer fd.Close()
  while True:
    say 'YYY cat1 fd.Read', fd
    buf, eof = fd.Read(BS)
    say 'YYY cat1 fd.Read', buf, eof
    say 'YYY calling aphid.WrapWrite', len(buf), buf
    if buf:
      aphid.WrapWrite(os.Stdout, buf)  # Writes fully.
    say 'YYY called aphid.WrapWrite', len(buf), buf
    if eof:
      break
  pass

def Cat(args):
  for arg in args:
    cat1(arg)
  pass

Ensemble = { 'test1': Test1, 'cat': Cat, }

def main(args):
  if not len(args):
    say 'Expected an Emsemble argument:', [k for k in Ensemble]
    os.Exit(13)

  cmd, args = args[0], args[1:]
  f = Ensemble.get(cmd)
  if not f:
    say "No such command:", cmd
    os.Exit(11)

  f(args)

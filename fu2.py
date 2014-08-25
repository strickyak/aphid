#from go import fmt
from go import os
from go import path/filepath

from . import A
from . import flag
from . import afs2
from . import rfs2

J = filepath.Join

def Test1(args):
  fs = rfs2.RfsClient2('localhost:9876', rfs2.KEYNAME, rfs2.KEY)

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

def cat1(path, out):
  fd = afs2.Open(path)
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
    out = afs2.Create(CREATE)
    defer out.Close()
  if APPEND:
    must not CREATE
    out = afs2.Append(APPEND)
    defer out.Close()
  if not out:
    out = afs2.Append('/Std/out')
  for arg in args:
    cat1(arg, out)
  pass


def FindFiles(args):
  for a in args:
    for name, isDir, mtime, sz in FindFiles1(a):
      print '%s %v %d %d' % (name, isDir, mtime, sz)

def FindFiles1(top):
  say '<<<', top
  try:
    d = afs2.Open(top)
  except as ex:
    # os.Stderr.Write('fu find: Cannot Open (%s): %q' % (ex, top))
    # fmt.Fprintf(os.Stderr, 'fu find: Cannot Open (%s): %q\n', ex, top)
    A.Err('fu find: Cannot Open (%s): %q\n', ex, top)
    A.SetStatus(2)
    return
  defer d.Close()
  try:
    for name, isDir, mtime, sz in d.List():
      say 'FFFFFF', name, isDir, mtime, sz
      jname = J(top, name)
      say 'FFFFFFJ', jname, isDir, mtime, sz
      if isDir:
        for x in FindFiles1(jname):
          yield x
      else:
        yield jname, isDir, mtime, sz
  except as ex:
    # os.Stderr.Write('fu find: Cannot List (%s): %q' % (ex, top))
    A.Err('fu find: Cannot List (%s): %q' % (ex, top))
    A.SetStatus(2)
    return

def Sync(args):
  pass

Ensemble = { 'test1': Test1, 'cat': Cat, 'find': FindFiles }

CREATE = flag.String('create', '', 'Create output file with "cat" command.')
APPEND = flag.String('append', '', 'Append output file with "cat" command.')

def main(args):
  global CREATE, APPEND
  args = flag.Take(args)
  CREATE = CREATE()
  APPEND = APPEND()

  if not len(args):
    say 'Expected an Emsemble argument:', [k for k in Ensemble]
    os.Exit(13)

  cmd, args = args[0], args[1:]
  f = Ensemble.get(cmd)
  if not f:
    say "No such command:", cmd
    os.Exit(11)

  f(args)
  A.Exit(0)

# DEMO:
#   rye run rfs.py *.py -- -port=9988 -root=/etc  &
#   rye run fu.py *.py  -- --rfs=127.0.0.1:9988 find /There/localhost:9988/java

import go/os
import go/path/filepath

import ./A
import ./flag
import ./afs
import ./rfs

J = filepath.Join

def Test1(args):
  fs = rfs.RfsClient(RFS.X, rfs.KEYNAME, rfs.KEY)

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
  fd = afs.Open(path)
  #say 'YYY cat1', fd
  with defer fd.Close():
    while True:
      #say 'YYY cat1 fd.Read', fd
      buf, eof = fd.Read(BS)
      #say 'YYY cat1 fd.Read', buf, eof
      if buf:
        ### aphid.WrapWrite(out, buf)  # Writes fully.
        n = len(buf)
        while n > 0:
          c = out.Write(buf)
          buf = buf[c:]
          n -= c
          #say 'YYYYYYYY', n, c
      #say 'YYY called aphid.WrapWrite', len(buf), buf
      if eof:
        break
    pass
  pass

def Cat(args):
  w = None
  if CREATE.X:
    must not APPEND.X
    w = afs.Create(CREATE.X)
  if APPEND.X:
    must not CREATE.X
    w = afs.Append(APPEND.X)
  if not w:
    w = afs.Append('/Std/out')
  with defer w.Close():
    for arg in args:
      cat1(arg, w)
  pass

def Cp(args):
  src, dst = args
  Copy1File(src, dst)

def Copy1File(src, dst):
  r = afs.Open(src)
  with defer r.Close():
    w = afs.Create(dst) 
    with defer w.Close():
      cat1(src, w)
      mt = r.ModTime()
      afs.SetModTime(dst, mt)

def FindFiles(args):
  for a in args:
    for name, isDir, mtime, sz in FindFiles1(a, ''):
      print '%s %s %d %d' % (J(a, name), 'D' if isDir else 'F', mtime, sz)

def FindFiles1(top, subdir):
  path = J(top, subdir)
  try:
    d = afs.Open(path)
  except as ex:
    A.Err('fu find: Cannot Open (%s): %q\n' % (ex, path))
    A.SetExitStatus(2)
    return
  with defer d.Close():
    try:
      for name, isDir, mtime, sz in sorted(d.List()):
        jname = J(subdir, name)
        yield jname, isDir, mtime, sz
        if isDir:
          for x in FindFiles1(top, jname):
            yield x
    except as ex:
      A.Err('fu find: Cannot List (%s): %q' % (ex, top))
      A.SetExitStatus(2)
      return

def Sync(args):
  if len(args) != 2:
    A.Err('fu sync: To perform a sync, we need a destination and a path.')
    A.SetExitStatus(2)
    return
  source, dest = args

  nf, nd = 0, 0
  for path, isDir, why in Sync1(source, dest):
    print path, 'D' if isDir else 'F', why
    if isDir:
      nd += 1
    else:
      nf += 1
      if YES.X:
        Copy1File(J(source, path), J(dest, path))
  A.Info('Need to make %d directories. copy %d files.' % (nd, nf))

# rye run fu.py *.py -- sync /Here/static_test_src /Here/static_test_dst
def Sync1(source, dest):
  dst_promise = go FindFiles1(dest, '')
  src_promise = go FindFiles1(source, '')
  dst_files = dst_promise.Wait()
  src_files = src_promise.Wait()

  dest_dict = {}
  for path, isDir, mtime, size in dst_files:
    dest_dict[path] = (isDir, mtime, size)

  for path, isDir, mtime, size in src_files:
    d = dest_dict.get(path)
    if not d:
      yield path, isDir, 'MISSING'
    elif not isDir:
      _isDir, _mtime, _size = d
      if isDir != _isDir:
        yield path, isDir, 'isDir'
      elif size != _size:
        yield path, isDir, 'size'
      elif mtime != _mtime:
        yield path, isDir, 'mtime'
      else:
        pass
    else:
      pass
  

Ensemble = {
    'test1': Test1,
    'cat': Cat,
    'cp': Cp,
    'find': FindFiles,
    'sync': Sync,
}

CREATE = flag.String('create', '', 'Create output file with "cat" command.')
APPEND = flag.String('append', '', 'Append output file with "cat" command.')
RFS    = flag.String('rfs', 'localhost:9876', 'Location of rfs server')
YES    = flag.Bool(  'y', False, 'Really sync.')

def main(args):
  args = flag.Munch(args)

  if not len(args):
    say 'Expected an Emsemble argument:', [k for k in Ensemble]
    os.Exit(13)

  cmd, args = args[0], args[1:]
  f = Ensemble.get(cmd)
  if not f:
    A.Err("Available commands: %v" % repr(sorted(Ensemble.keys())))
    A.Fatal("No such command: %q" % cmd)
    os.Exit(11)

  f(args)
  A.Exit(0)

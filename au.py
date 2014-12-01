from go import bytes, io, os, time
from go import io/ioutil, path/filepath

from . import A, flag, keyring, rbundle

J = filepath.Join
FPERM = 0644
DPERM = 0755

def Push(args):
  stop = J(DIR.X, BUND.X, 'STOP')  # Build prefix plus word 'STOP'.
  prefix_len = len(stop) - 4  # Without the 'STOP'.

  def fn(path, info, err):
    if err is None and not info.IsDir():
      short_path = path[prefix_len:]
      say path, short_path
      client.RWriteFile(BUND.X, short_path, ioutil.ReadFile(path))

  say 'filepath.Walk', J(DIR.X, BUND.X)
  filepath.Walk(J(DIR.X, BUND.X), fn)
  say 'filepath.Walk DONE.'

def Pull(args):
  if not args:
    args = ['/']
  for a in args:
    for name, isDir, mtime, sz in FindFiles1(a):
      jname = J(DIR.X, BUND.X, name)
      if isDir:
        os.MkdirAll(jname, DPERM)
      else:
        b = client.RReadFile(BUND.X, name)
        ioutil.WriteFile(jname, b, FPERM)
        t = time.Unix(mtime, 0)
        os.Chtimes(jname, t, t)

def Cat(args):
  for name in args:
    b = client.RReadFile(BUND.X, name)
    io.Copy(os.Stdout, bytes.NewReader(b))

def Find(args):
  if not args:
    args = ['/']
  for a in args:
    for name, isDir, mtime, sz in FindFiles1(a):
      print '%s %10d %10d %s' % ('D' if isDir else 'F', mtime, sz, name)

def FindFiles1(path):
  try:
    for name, isDir, mtime, sz in sorted(client.RList4(BUND.X, path)):
      jname = J(path, name)
      yield jname, isDir, mtime, sz
      if isDir:
        for x in FindFiles1(jname):
          yield x
  except as ex:
    A.Err('fu find: Cannot List (%s): %q' % (ex, path))
    A.SetExitStatus(2)

#def Sync(args):
#  if len(args) != 2:
#    A.Err('fu sync: To perform a sync, we need a destination and a path.')
#    A.SetExitStatus(2)
#    return
#  source, dest = args
#
#  nf, nd = 0, 0
#  for path, isDir, why in Sync1(source, dest):
#    print path, 'D' if isDir else 'F', why
#    if isDir:
#      nd += 1
#    else:
#      nf += 1
#      if YES.X:
#        Copy1File(J(source, path), J(dest, path))
#  A.Info('Need to make %d directories. copy %d files.' % (nd, nf))
#
## rye run fu.py *.py -- sync /Here/static_test_src /Here/static_test_dst
#def Sync1(source, dest):
#  dst_promise = go FindFiles1(dest, '')
#  src_promise = go FindFiles1(source, '')
#  dst_files = dst_promise.Wait()
#  src_files = src_promise.Wait()
#
#  dest_dict = {}
#  for path, isDir, mtime, size in dst_files:
#    dest_dict[path] = (isDir, mtime, size)
#
#  for path, isDir, mtime, size in src_files:
#    d = dest_dict.get(path)
#    if not d:
#      yield path, isDir, 'MISSING'
#    elif not isDir:
#      _isDir, _mtime, _size = d
#      if isDir != _isDir:
#        yield path, isDir, 'isDir'
#      elif size != _size:
#        yield path, isDir, 'size'
#      elif mtime != _mtime:
#        yield path, isDir, 'mtime'
#      else:
#        pass
#    else:
#      pass
  

Ensemble = {
    'find': Find,
    'cat': Cat,
    'pull': Pull,
    'push': Push,
}

BUND = flag.String('bund', '', 'Remote bundle name.')
DIR = flag.String('dir', '', 'Local directory to push or pull.')
SERVER = flag.String('server', 'localhost:8081', 'Location of bundle server')
YES    = flag.Bool('y', False, 'Really sync.')
CID    = flag.String('cid', '91', 'Client DH ID.')
SID    = flag.String('sid', '92', 'Server DH ID.')
RING    = flag.String('ring', 'test.ring', 'Keyring File.')

def main(args):
  global client
  args = flag.Munch(args)
  keyring.Load(RING.X, keyring.Ring)
  client = rbundle.RBundleClient(SERVER.X, keyring.Ring, CID.X, SID.X)

  if not len(args):
    say 'Expected an Emsemble argument:', [k for k in Ensemble]
    os.Exit(13)

  cmd = args.pop(0)
  f = Ensemble.get(cmd)
  if not f:
    A.Err("Available commands: %v" % repr(sorted(Ensemble.keys())))
    A.Fatal("No such command: %q" % cmd)
    os.Exit(11)

  f(args)
  A.Exit(0)

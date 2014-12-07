from go import bytes, io, os, time
from go import io/ioutil, path/filepath

from . import A, flag, keyring, rbundle

J = filepath.Join
FPERM = 0644
DPERM = 0755

def BigLocalDir(_):
  z = {}
  fnord = J(DIR.X, BUND.X, 'FNORD')  # Build prefix plus word 'FNORD'.
  prefix_len = len(fnord) - 5  # Without the 'FNORD'.

  def fn(path, info, err):
    if err is None and not info.IsDir():
      short_path = path[prefix_len:]
      z[short_path] = (info.ModTime().Unix(), info.Size())

  filepath.Walk(J(DIR.X, BUND.X), fn)
  for k, v in sorted(z.items()):
    print k, v
  return z

def BigRemoteDir(_):
  z = {}
  for name, isDir, mtime, sz in FindFiles1('/'):
    if not isDir:
      name = name.lstrip('/')
      z[name] = (mtime, sz)
  for k, v in sorted(z.items()):
    print k, v
  return z

def BigDirs():
  lo = go BigLocalDir([])
  re = go BigRemoteDir([])
  return lo.Wait(), re.Wait()

def NewPull(args):
  lo, re = BigDirs()

  for k, v in sorted(re.items()):
    mtime, size = v
    v2 = lo.get(k)
    if v2 == v:
      continue  # Don't copy if mtime & size are same.

    jname = J(DIR.X, BUND.X, k)
    b = client.RReadFile(BUND.X, k)
    os.MkdirAll(filepath.Dir(jname), DPERM)
    ioutil.WriteFile(jname, b, FPERM)
    t = time.Unix(mtime, 0)
    os.Chtimes(jname, t, t)

def NewPush(args):
  lo, re = BigDirs()

  for k, v in sorted(lo.items()):
    mtime, size = v
    v2 = re.get(k)
    if v2 == v:
      continue  # Don't copy if mtime & size are same.
      
    say k, mtime, size, v2
    jname = J(DIR.X, BUND.X, k)
    client.RWriteFile(BUND.X, k, ioutil.ReadFile(jname), mtime=mtime)

def Push(args):
  fnord = J(DIR.X, BUND.X, 'FNORD')  # Build prefix plus word 'FNORD'.
  prefix_len = len(fnord) - 5  # Without the 'FNORD'.

  def fn(path, info, err):
    if err is None and not info.IsDir():
      short_path = path[prefix_len:]
      mtime = info.ModTime().Unix()
      say path, short_path
      client.RWriteFile(BUND.X, short_path, ioutil.ReadFile(path), mtime=mtime)

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

Ensemble = {
    'find': Find,
    'cat': Cat,
    'pull': Pull,
    'push': Push,
    'newpull': NewPull,
    'newpush': NewPush,
    'BigLocalDir': BigLocalDir,
    'BigRemoteDir': BigRemoteDir,
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

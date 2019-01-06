from go import bufio, bytes, io, os, time
from go import io.ioutil, path.filepath

import A, bundle, flag, keyring, rbundle, sym

J = filepath.Join
FPERM = 0644
DPERM = 0755

def BigLocalDir(_):
  z = {}
  fnord = J(DIR.X, BUND.X, 'FNORD')  # Build prefix plus word 'FNORD'.
  prefix_len = len(fnord) - 5  # Without the 'FNORD'.

  def fn(path, info, err):
    say path, info, err, info.IsDir() if info else None
    if err is None and not info.IsDir():
      short_path = path[prefix_len:]
      z[short_path] = (info.ModTime().Unix(), info.Size())
      say short_path

  say 'filepath.Walk(', J(DIR.X, BUND.X),' fn)'
  filepath.Walk(J(DIR.X, BUND.X), fn)
  i = 0
  for k, v in sorted(z.items()):
    print k, v, '[%s]local' % J(DIR.X, BUND.X)
    i += 1
  say 'Listed %d files' % i
  return z

def BigRemoteDir(_):
  say 'HHHHHHHHHHHHHHHHHHHHELLO'
  z = {}
  for name, isDir, mtime, sz in FindFiles1('/'):
    if not isDir:
      name = name.lstrip('/')
      z[name] = (mtime, sz)
  i = 0
  for k, v in sorted(z.items()):
    print k, v, '[%s]remote' % BUND.X
    i += 1
  say 'Listed %d files' % i
  return z

def BigDirs():
  #lo = go BigLocalDir([])
  #re = go BigRemoteDir([])
  #return lo.Wait(), re.Wait()
  lo = BigLocalDir([])
  re = BigRemoteDir([])
  return lo, re

def NewPull(args):
  lo, re = BigDirs()

  for k, v in sorted(re.items()):
    mtime, size = v
    v2 = lo.get(k)
    if v2 == v:
      continue  # Don't copy if mtime & size are same.

    jname = J(DIR.X, BUND.X, k)
    CopyRemoteFileHere(from_there=k, to_here=jname, mtime=mtime)

def NewPush(args):
  lo, re = BigDirs()

  for k, v in sorted(lo.items()):
    mtime, size = v
    v2 = re.get(k)
    if v2 == v:
      continue  # Don't copy if mtime & size are same.
      
    say 'WRITING', k, mtime, size, v2
    jname = J(DIR.X, BUND.X, k)
    client.RWriteFile(BUND.X, k, ioutil.ReadFile(jname), mtime=mtime, pw=PW.X)

def SPull(args):
  dLocal, dRemote = BigDirs()  # Dicts mapping path to (mtime, size)

  for path, remoteStats in sorted(dRemote.items()):
    mtime, size = remoteStats
    localMTimeSize = dLocal.get(path)
    if localMTimeSize == remoteStats:
      continue  # Don't copy if mtime & size are same.
      
    say 'READING', path, mtime, size, localMTimeSize
    pullFile(path, J(DIR.X, BUND.X, path), mtime=mtime)

def SPush(args):
  dLocal, dRemote = BigDirs()  # Dicts mapping path to (mtime, size)

  for path, localStats in sorted(dLocal.items()):
    mtime, size = localStats
    remoteMTimeSize = dRemote.get(path)
    if remoteMTimeSize == localStats:
      continue  # Don't copy if mtime & size are same.
      
    say 'WRITING', path, mtime, size, remoteMTimeSize
    pushFile(J(DIR.X, BUND.X, path), path, mtime=mtime)

def Push(args):
  fnord = J(DIR.X, BUND.X, 'FNORD')  # Build prefix plus word 'FNORD'.
  prefix_len = len(fnord) - 5  # Without the 'FNORD'.
  say fnord, prefix_len

  def fn(path, info, err):
    if err is None and not info.IsDir():
      say path, fnord, prefix_len
      short_path = path[prefix_len:]
      mtime = info.ModTime().Unix()
      say 'WRITING', path, short_path
      client.RWriteFile(BUND.X, short_path, ioutil.ReadFile(path), mtime=mtime, pw=PW.X)

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
        CopyRemoteFileHere(from_there=name, to_here=jname, mtime=mtime)

def Cat(args):
  for name in args:
    CopyRemoteFileHere(from_there=name, to_here='/dev/stdout', mtime=None)

# TODO: CopyRemoteFileHere & pullFile are almost the same.
def CopyRemoteFileHere(from_there, to_here, mtime):
  os.MkdirAll(filepath.Dir(to_here), DPERM)
  r = client.RemoteOpen(BUND.X, path=from_there, pw=PW.X, raw=False)
  fd = os.Create(to_here)
  w = bufio.NewWriter(fd)
  bundle.CopyChunks(bundle.ChunkWriterAdapter(w), r)
  w.Flush()
  fd.Close()
  if mtime:
    say mtime
    if mtime > 1000000000009:
      t = time.Unix(0, mtime * 1000000)
    else:
      t = time.Unix(mtime, 0)
    say t, to_here
    os.Chtimes(to_here, t, t)

# TODO: CopyRemoteFileHere & pullFile are almost the same.
def pullFile(src, dest, mtime=None):
    r = client.RemoteOpen(BUND.X, src, pw=PW.X, raw=False)
    os.MkdirAll(filepath.Dir(dest), 0777)
    w = os.Create(dest)
    io.Copy(w, r)
    w.Close()
    r.Close()
    now = time.Now()
    mtime = mtime if mtime else now 
    os.Chtimes(dest, now, time.Unix(0, 1000000*mtime))
  
def pushFile(src, dest, mtime):
    r = os.Open(src)
    w = client.RemoteCreate(BUND.X, dest, pw=PW.X, mtime=mtime, raw=False)
    io.Copy(w, r)
    w.Close()
    r.Close()

def SCat(args):
  for name in args:
    pullFile(name, '/dev/stdout', mtime=None)

def RawCat(args):
  for rawpath in args:
    b = client.RReadRawFile(BUND.X, rawpath=rawpath)
    io.Copy(os.Stdout, bytes.NewReader(b))

def RawWrite(args):
  must len(args) == 2
  rawpath, data = args
  client.RWriteRawFile(BUND.X, rawpath=rawpath, data=byt(data))

def SWrite(args):
  src, dest = args
  pushFile(src, dest, MTIME.X)

def Find(args):
  if not args:
    args = ['/']
  for a in args:
    for name, isDir, mtime, sz in FindFiles1(a):
      print '%s %10d %10d %s' % ('D' if isDir else 'F', mtime, sz, name)

def FindFiles1(path):
  try:
    for name, isDir, mtime, sz in sorted(client.RList4(BUND.X, path, pw=PW.X)):
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
    'SCat': SCat,
    'rawcat': RawCat,
    'rawwrite': RawWrite,
    'SWrite': SWrite,
    'SPull': SPull,
    'SPush': SPush,
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
EXIT   = flag.Int('exit', 1, 'Exit at end of main()')
PW     = flag.String('pw', '', 'Web password')
MTIME  = flag.Int('mtime', 0, 'Mtime of file creation')

def main(args):
  global client
  args = flag.Munch(args)
  keyring.Load()
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

  print >>os.Stderr, "\n%s -- START -- %s -- %s\n" % (f, cmd, args)
  f(args)
  print >>os.Stderr, "\n%s -- OKAY -- %s -- %s\n" % (f, cmd, args)
  if EXIT.X:
    A.Exit(0)

from go import bufio, bytes, io, os, regexp, time
from go import io.ioutil, path as P, path.filepath as FP

import A, bundle, flag, keyring, rbundle, sym

FPERM = 0644
DPERM = 0755

client = flag.String('c', 'client', 'name of client in keyring')
server = flag.String('s', 'server', 'name of server in keyring')

class FileBase:
  pass

class BundleFile(FileBase):
  pass

class RemoteFile(FileBase):
  def __init__(hostport, bname, path):
    .hostport = hostport
    .bname = bname
    .path = path
    #say keyring.Ring.keys()
    #say .hostport, client.X, server.X
    .remote = rbundle.RBundleClient(.hostport, keyring.Ring, client.X, server.X)

  def List4():
    return .remote.RList4(.bname, .path, pw=None)

  def Open():
    return .remote.RemoteOpen(.bname, .path, pw=None, raw=False)

  def Create():
    now = time.Now().UnixNano() / 1000000  # ms
    return .remote.RemoteCreate(.bname, .path, pw=None, raw=False, mtime=now)

  def Close():
    .remote.Close()

class LocalFile(FileBase):
  def __init__(path):
    .path = path

  def List4():
    fd = os.Open(.path)
    infos = fd.Readdir(-1)
    def results():
      for info in infos:
        name, dr, mt, sz = info.Name(), info.IsDir(), info.ModTime(), info.Size()
        def check(name:str, dr:bool, mt, sz:int):
          pass
        check(name, dr, mt, sz)
        if sz:
          yield name + ('/' if dr else ''), dr, mt, sz
    return sorted(results())

  def Open():
    return os.Open(.path)

  def Create():
    return os.Create(.path)

  def Close():
    pass

MATCH_BUNDLE = regexp.MustCompile(`^/+bundle\b`).FindString
PARSE_BUNDLE = regexp.MustCompile(`^/+bundle/([^@]+)/@/([-a-z0-9_]+)(/.*)?$`).FindStringSubmatch

MATCH_REMOTE = regexp.MustCompile(`^/+remote\b`).FindString
PARSE_REMOTE = regexp.MustCompile(`^/+remote/([-A-Za-z0-9.]+(?:[:][0-9]+)?)/([-a-z0-9_]+)(/.*)?$`).FindStringSubmatch

def FileFactory(path: str) -> FileBase:
  ww = P.Split(path)
  must ww, 'Empty filepath not allowed'
  switch:
    case MATCH_BUNDLE(path):
      _, top, bname, within = PARSE_BUNDLE(path)
      return BundleFile(top, bname, within)
    case MATCH_REMOTE(path):
      _, hostport, bname, within = PARSE_REMOTE(path)
      hostport = hostport if (':' in hostport) else '%s:81' % hostport
      return RemoteFile(hostport, bname, within)
    default:
      return LocalFile(path)

USAGE = `Usage:
  vfs ls Dir
  vfs cp FromDir ToDir

  Dirs are
    /remote/host:post/bundlename/path/within/bundle
    /bundle/absolute/path/to/bundle/@/bundlename/path/within/bundle
    /absolute/path/to/local/dir
    relative/path/to/local/dir
`

def RunCommand(args):
  if not args:
    args = ['help']

  cmd, args = args[0], args[1:]
  switch cmd:
    case 'ls':
      for a in args:
        print "%s :" % a
        f = FileFactory(a)
        for name, dr, mt, sz in f.List4():
          print "\t%s" % name
        f.Close()

    case 'cat':
      for a in args:
        f = FileFactory(a)
        r = f.Open()
        io.Copy(os.Stdout, r)
        r.Close()

    case 'create':
      must len(args) == 1, args
      f = FileFactory(args[0])
      w = f.Create()
      io.Copy(w, os.Stdin)
      w.Close()
      f.Close()

    default:
      print >> os.Stderr, USAGE
      os.Exit(2)

def main(args):
  args = flag.Munch(args)
  if keyring.RingFilename:
    keyring.Load(keyring.RingFilename.X)
  RunCommand(args)

  #try:
  #  RunCommand(args)
  #except as ex:
  #  print >> os.Stderr, "ERROR: %s" % ex
  #  os.Exit(2)

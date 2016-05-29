from go import bufio, bytes, io, os, regexp, time
from go import io/ioutil, path as P, path/filepath as FP

from . import A, bundle, flag, keyring, rbundle, sym

FPERM = 0644
DPERM = 0755

class FileBase:
  pass

class BundleFile(FileBase):
  pass

class RemoteFile(FileBase):
  pass

class LocalFile(FileBase):
  def __init__(path):
    .path = path

  def Dir():
    fd = os.Open(.path)
    infos = fd.Readdir(-1)
    def results():
      for info in infos:
        name, sz, mt, dr = info.Name(), info.Size(), info.ModTime(), info.IsDir()
        def check(name:str, sz:int, mt, dr:bool):
          pass
        check(name, sz, mt, dr)
        if sz:
          yield name + ('/' if dr else ''), sz, mt, dr
    return sorted(results())

  def Open():
    return os.Open(.path)

  def Create():
    return os.Create(.path)

MATCH_BUNDLE = regexp.MustCompile('^/+bundle/').FindString
PARSE_BUNDLE = regexp.MustCompile('^/+bundle/([^@]+)/@/([a-z0-9_]+)(/.*)?$').FindStringSubmatch

MATCH_REMOTE = regexp.MustCompile('^/+remote/').FindString
PARSE_REMOTE = regexp.MustCompile('^/+remote/([-A-Za-z0-9.]+)(:([0-9]+))?/([a-z0-9_]+)(/.*)?$').FindStringSubmatch

def FileFactory(path: str) -> FileBase:
  ww = P.Split(path)
  must ww, 'Empty filepath not allowed'
  switch:
    case MATCH_BUNDLE(path):
      top, bname, within = PARSE_BUNDLE(path)
      return BundleFile(top, bname, within)
    case MATCH_REMOTE(path):
      host, _, port, bname, within = PARSE_BUNDLE(path)
      port = port if port else '81'
      return RemoteFile(host, int(port), bname, within)
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
        for name, sz, mt, dr in f.Dir():
          print "\t%s" % name

    case 'cat':
      for a in args:
        f = FileFactory(a)
        r = f.Open()
        io.Copy(os.Stdout, r)
        r.Close()

    case 'create':
      must len(args) == 1, args
      f = FileFactory(a)
      w = f.Create()
      io.Copy(w, os.Stdin)
      w.Close()

    default:
      print >> os.Stderr, USAGE
      os.Exit(2)

def main(args):
  try:
    RunCommand(args)
  except as ex:
    print >> os.Stderr, "ERROR: %s" % ex
    os.Exit(2)

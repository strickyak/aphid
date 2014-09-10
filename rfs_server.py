from go import os
from go import path/filepath

from go import github.com/strickyak/aphid

from . import rpc
from . import flag

PORT = flag.Int('port', 0, 'Port to listen on')
ROOT = flag.String('root', '', 'File system root')

def localPath(path):
  return filepath.Join(ROOT.X, path)

def AReadAt(path, n, pos):
  say 'YYY <<< AReadAt', path, n, pos
  fd = os.Open(localPath(path))
  defer fd.Close()
  buf, eof = aphid.WrapReadAt(fd, n, pos)
  say 'YYY >>> AReadAt', buf, eof
  return buf, eof

def AWriteAt(path, data, pos):
  fd = os.OpenFile(localPath(path), os.O_WRONLY | os.O_CREATE, 0666)
  defer fd.Close()
  return fd.WriteAt(data, pos)

def AListDir(path):
  fd = os.Open(localPath(path))
  defer fd.Close()
  vec = fd.Readdir(-1)
  z = [(i.Name(), i.IsDir(), i.Size(), i.ModTime().Unix()) for i in vec]
  return z

def main(argv):
  argv = flag.Munch(argv)

  say ROOT
  say PORT
  r = rpc.Dial('localhost:%d' % PORT.X)
  r.Register1('AListDir', AListDir)
  r.Register3('AReadAt', AReadAt)
  r.Register3('AWriteAt', AWriteAt)
  r.ListenAndServe()

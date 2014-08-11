from go import flag
from go import os
from go import path/filepath

from . import rpc
from . import wrap_io

PORT = flag.Int('port', 0, 'Port to listen on')
ROOT = flag.String('root', '', 'File system root')

def localPath(path):
  return filepath.Join(ROOT, path)

def ReadAt(path, n, pos):
  fd = os.Open(localPath(path))
  defer fd.Close()
  buf, eof = wrap_io.ReadAtCommaEof(fd, n, pos)
  return buf, eof

def WriteAt(path, data, pos):
  fd = os.OpenFile(localPath(path), os.O_WRONLY | os.O_CREATE, 0666)
  defer fd.Close()
  return fd.WriteAt(data, pos)

def ListDir(path):
  fd = os.Open(localPath(path))
  defer fd.Close()
  vec = fd.Readdir(-1)
  z = [(i.Name(), i.IsDir(), i.Size(), i.ModTime().Unix()) for i in vec]
  return z

def main(argv):
  global PORT, ROOT
  flag.Parse()
  PORT = int(goreify(goderef(PORT)))
  ROOT = str(goreify(goderef(ROOT)))

  r = rpc.Dial('localhost:%d' % PORT)
  r.Register1('ListDir', ListDir)
  r.Register3('ReadAt', ReadAt)
  r.Register3('WriteAt', WriteAt)
  list(r.GoListenAndServe())  # never yields.

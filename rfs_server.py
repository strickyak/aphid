from go import flag
from go import os
#from go import time
from go import path/filepath

import github.com/strickyak/aphid/rpc

port = flag.Int('port', 0, 'Port to listen on')
root = flag.String('root', '', 'File system root')

def localPath(path):
  return filepath.Join(str(goreify(goderef(root))), path)

def Get(path, pos, n):
  fd = os.Open(localPath(path))
  p0 = fd.Seek(pos, 0)
  assert p0 == pos
  buf = byt(n)
  assert len(buf) == n
  count = fd.Read(buf)
  fd.Close()
  return buf[:count]

def List(path):
  fd = os.Open(localPath(path))
  vec = fd.Readdir(-1)
  fd.Close()
  z = [(i.Name(), i.IsDir(), i.Size(), i.ModTime().Unix()) for i in vec]
  return z

def main(argv):
  flag.Parse()
  r = rpc.Dial('localhost:%d' % int(goreify(goderef(port))))
  r.Register1('List', List)
  r.Register3('Get', Get)
  wait = r.GoListenAndServe()
  list(wait)
  # time.Sleep(24 * time.Hour)

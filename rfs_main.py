from go import os
from go import time

import github.com/strickyak/aphid/rpc

DIAL = 'localhost:8080'

def Get(path, pos, n):
  fd = os.Open(a[path])
  p0 = fd.Seek(pos, 0)
  assert p0 == pos
  buf = byt(n)
  assert len(buf) == n
  count = fd.Read(buf)
  return buf[:count]
  

def List(path):
  fd = os.Open(path)
  vec = fd.Readdir(-1)
  z = [(i.Name(), i.IsDir(), i.Size(), i.ModTime().Unix()) for i in vec]
  say z
  return z
   
def main(argv):
  r = rpc.Dial(DIAL)
  r.Register1('List', List)
  r.Register3('Get', Get)
  wait = r.GoListenAndServe()

  time.Sleep(10 * time.Millisecond)

  say r.Call1('List', '.')

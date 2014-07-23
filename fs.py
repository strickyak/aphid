from go import os
from go import time

import github.com/strickyak/aphid/rpc

DIAL = 'localhost:8080'

def List(path):
  #fd = os.NewFile(path)
  fd = os.Open(path)
  vec = fd.Readdir(-1)
  z = [(i.Name(), i.IsDir(), i.Size(), i.ModTime().Unix()) for i in vec]
  say z
  return z
   
def main(argv):
  r = rpc.Dial(DIAL)
  r.Register('List', List)
  wait = r.GoListenAndServe()

  time.Sleep(10 * time.Millisecond)

  say r.Call1('List', '.')

from go import os
from go import time
import rfs

import github.com/strickyak/aphid/rpc
   
def main(argv):
  r = rpc.Dial(WHERE)
  r.Register1('List', rfs.List)
  r.Register3('Get', rfs.Get)
  wait = r.GoListenAndServe()

  time.Sleep(10 * time.Millisecond)

  say r.Call1('List', '.')

from go import os
from go import time
from . import rfs
from . import rpc
   
def main(argv):
  r = rpc.Dial(WHERE)
  r.Register1('List', rfs.List)
  r.Register3('Get', rfs.Get)
  go r.ListenAndServe()

  time.Sleep(10 * time.Millisecond)

  say r.Call1('List', '.')

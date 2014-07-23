from go import time

import github.com/strickyak/aphid/rpc

def Double(x):
  return x + x
   
def main(argv):
  r = rpc.Dial('localhost:8080')
  r.Register('Twice', Double)
  wait = r.GoListenAndServe()

  time.Sleep(10 * time.Millisecond)

  assert 2468 == r.Call1('Twice', 1234)
  assert 'DuranDuran' == r.Call1('Twice', 'Duran')

  say 'OKAY'

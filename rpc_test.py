from go import math/big
from go import time

import github.com/strickyak/aphid/rpc

def Double(x):
  return x + x
   
def product(x, y):
  return x * y
   
def PowMod(x, y, m):
  xx = big.NewInt(0)
  yy = big.NewInt(0)
  mm = big.NewInt(0)
  zz = big.NewInt(0)
  xx, ok = xx.SetString(x, 10)
  assert ok, x
  yy, ok = yy.SetString(y, 10)
  assert ok, y
  mm, ok = mm.SetString(m, 10)
  assert ok, m
  zz = zz.Exp(xx, yy, mm)
  return zz.String()

def main(argv):
  r = rpc.Dial('localhost:8080')
  r.Register1('Twice', Double)
  r.Register2('Product', product)
  r.Register3('PowMod', PowMod)
  wait = r.GoListenAndServe()

  time.Sleep(10 * time.Millisecond)

  assert 2468 == r.Call1('Twice', 1234)
  assert 'DuranDuran' == r.Call1('Twice', 'Duran')

  assert 42 == r.Call2('Product', 7, 6)

  assert '1' == r.Call3('PowMod', '100', '3', '999999')

  say 'OKAY'

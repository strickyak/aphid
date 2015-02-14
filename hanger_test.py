from . import hanger
from . import A

hanger.TIMEOUT = 2

class Zebra:
  def __init__():
    .i = 0
  def incr(x):
    .i += x
  def get():
    return .i

def main(_):
  h = hanger.Hanger()
  z = Zebra()
  id = h.Hang(z)
  for i in range(10):
    h.Invoke(id, i+i, 'incr', i)
    A.Sleep(1.0)
    say h.Invoke(id, i+i+1, 'get')
  must 45 == h.Invoke(id, 20, 'get')
  A.Sleep(5.0)
  must except h.Invoke(id, 21, 'get')
  say 'OKAY: hanger_test.py'

from go import bufio, bytes, io
from go import net, sync, time
from go import crypto/rand

from . import dh, keyring
from . import rpc2 as RPC2

def DemoSum(*args):
  z = 0.0
  for a in args:
    z += float(a)
  return z

def DemoSleepAndDouble(millis):
  time.Sleep(millis * time.Millisecond)
  return 2 * millis

def main(args):
  ring1, ring2 = {}, {} # ring1 for client, ring2 for server.

  obj1 = dh.Forge('1', 'key1', dh.G3072)
  obj2 = dh.Forge('2', 'key2', dh.G3072)

  ring1['1'] = keyring.Line() {
    num:'1', name:'key1', kind:'dh',
    pub:dh.String(obj1.pub), sec:dh.String(obj1.sec), sym:None, base:None
  }
  ring1['2'] = keyring.Line() {
    num:'2', name:'key2', kind:'dh',
    pub:dh.String(obj2.pub), sec:None, sym:None, base:None
  }

  ring2['1'] = keyring.Line() {
    num:'1', name:'key1', kind:'dh',
    pub:dh.String(obj1.pub), sec:None, sym:None, base:None
  }
  ring2['2'] = keyring.Line() {
    num:'2', name:'key2', kind:'dh',
    pub:dh.String(obj2.pub), sec:dh.String(obj2.sec), sym:None, base:None
  }

  svr = RPC2.Server(':9999', ring=ring2)
  svr.Register('DemoSum', DemoSum)
  svr.Register('DemoSleepAndDouble', DemoSleepAndDouble)
  go svr.ListenAndServe()

  time.Sleep(100 * time.Millisecond)
  cli = RPC2.Client('localhost:9999', ring1, '1', '2')
  z = cli.Call('DemoSum', [100,200,300]).Wait()
  say z
  assert z == 600.0
  assert z == 600
  assert 600 == z

  d = {}
  for i in range(5):
    d[i] = cli.Call('DemoSleepAndDouble', [i * 100])
    say i, d[i]

  for i in range(5):
    say 'GGGGETTING', i, d[i]
    z = d[i].Wait()
    say 'GGGGOT', i, d[i], z
    assert z == i * 200

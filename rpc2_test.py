from go import bufio, bytes, io
from go import net, sync, time
from go import crypto.rand

import dh, keyring
import rpc2 as RPC2

def DemoSum(*args):
  z = 0.0
  say args, z
  for a in args:
    say a
    z += float(a)
    say z
  return z

def DemoSleepAndDouble(millis):
  time.Sleep(millis * time.Millisecond)
  return 2 * millis

def main(args):
  ring1, ring2 = {}, {} # ring1 for client, ring2 for server.

  obj1 = dh.Forge(dh.GROUP)
  obj2 = dh.Forge(dh.GROUP)

  ring1['1'] = dict(
    num='1', id='key1', TYPE='dh',
    pub=dh.String(obj1.pub), sec=dh.String(obj1.sec),
    )
  ring1['2'] = dict(
    num='2', id='key2', TYPE='dh',
    pub=dh.String(obj2.pub),
    )

  ring2['1'] = dict(
    num='1', id='key1', TYPE='dh',
    pub=dh.String(obj1.pub),
    )
  ring2['2'] = dict(
    num='2', id='key2', TYPE='dh',
    pub=dh.String(obj2.pub), sec=dh.String(obj2.sec),
    )

  svr = RPC2.Server(':9999', ring=keyring.CompileDicts(ring2))
  svr.Register('DemoSum', DemoSum)
  svr.Register('DemoSleepAndDouble', DemoSleepAndDouble)
  go svr.ListenAndServe()

  time.Sleep(100 * time.Millisecond)
  cli = RPC2.Client('localhost:9999', keyring.CompileDicts(ring1), '1', '2')
  z = cli.Call('DemoSum', *[100,200,300]).Wait()
  say z
  assert z == 600.0
  assert z == 600
  assert 600 == z

  d = {}
  for i in range(5):
    d[i] = cli.Call('DemoSleepAndDouble', *[i * 100])
    say i, d[i]

  for i in range(5):
    say 'GGGGETTING', i, d[i]
    z = d[i].Wait()
    say 'GGGGOT', i, d[i], z
    assert z == i * 200

from go import bufio
from go import net
from go import time
#from go import crypto/aes
#from go import crypto/cipher

from go import github.com/strickyak/aphid
from . import eval
from . import gcm

SerialCounter = 101
def Serial():
  global SerialCounter
  SerialCounter += 1
  return str(SerialCounter)

class Request:
  def __init__(proc, args):
    .proc = proc
    .args = args
    .serial = None
    .replyQ = aphid.NewChan(1)

def WriteChunk(w, data):
  say 'WriteChunk', w, data
  data = byt(data)
  bb = aphid.NewBuffer()
  bb.WriteChunk(data)
  z = bb.Bytes()
  w.Write(z)
  say 'WriteChunk Wrote', z

class Server2:
  def __init__(hostport, keyname, key):
    .hostport = hostport
    .keyname = keyname
    .procs = {}
    .sealer = gcm.Cipher(key)
    .outQ = aphid.NewChan(5)
    go .WriteActor()

  def Listen():
    .sock = net.Listen('tcp', .hostport)
    while True:
      conn = .sock.Accept()
      go .DoRead(conn)

  def WriteActor():
    while True:
      say 'WriteActor GGGGGetting...'
      tup = .outQ.Get()
      say 'WriteActor GGGGot', tup
      if tup is None:
        break
      conn, serial, result, err = tup
      say 'WriteActor GGGGot', conn, serial, result, err

      say serial, result, err
      p = .sealer.Seal(pickle( (serial, result, err) ), serial)
      say 'pickle', p
      say '... pickle', unpickle(p)
      WriteChunk(conn, p)
    .conn.Close()

  def DoRead(conn):
    r = bufio.NewReader(conn)
    while True:
      dark = ReadChunk(r)
      say 'DoRead', dark
      say 'DoRead', len(dark)
      pay, ser = .sealer.Open(dark)
      unp = unpickle(pay)
      serial, proc, args = unp
      must ser == serial
      say 'DoRead', serial, proc, args
      go .Execute(conn, serial, proc, args)

  def Execute(conn, serial, proc, args):
    say 'Execute GGGGGoing with Args', conn, serial, proc, args
    result, err = None, None
    try:
      fn = .procs.get(proc)
      if not fn:
        raise 'rpc2 function not registered in Server2', proc
      result = fn(*args)
    except as ex:
      err = ex
    say 'Execute GGGGGonna Put', conn, serial, result, err
    .outQ.Put( (conn, serial, result, err) )

  def Register(proc, fn):
    .procs[proc] = fn


class Client2:
  def __init__(hostport, keyname, key):
    .hostport = hostport
    .keyname = keyname
    .sealer = gcm.Cipher(key)
    .requests = {}
    .inQ = aphid.NewChan(5)
    .conn = net.Dial('tcp', hostport)
    go .ReadActor()
    go .WriteActor()

  def WriteActor():
    while True:
      req = .inQ.Get()
      if req is None:
        break

      # Allocate a serial, and remember the request.
      req.serial = Serial()
      .requests[req.serial] = req

      say 'pickle WA WC', req.serial, req.proc, req.args
      pay = pickle( (req.serial, req.proc, req.args) )
      say 'pickle WA WC', pay
      say 'pickle WA WC', len(pay)
      say '... pickle WA WC', unpickle(pay)
      dark = .sealer.Seal(pay, req.serial)
      WriteChunk(.conn, dark)

    .conn.Close()

  def ReadActor():
    r = bufio.NewReader(.conn)
    while True:
      # TODO -- when to stop.
      p = ReadChunk(r)
      say 'unpickle RRRRReadActor', p
      pay, ser = .sealer.Open(p)
      serial, result, err = unpickle(pay)
      must serial == ser # TODO
      say 'unpickle RRRRReadActor', serial, result, err 
      .requests[serial].replyQ.Put( (result, err) )
      say 'RRRRReadActor Put on Q', serial, result, err 


  def Call(proc, args):
    req = Request(proc, args)
    .inQ.Put(req)
    return Promise(req.replyQ)

class Promise:
  def __init__(chan):
    .chan = chan

  def Wait():
    #say 'WWWWaiting', .chan
    result, err = .chan.Get()
    #say 'WWWWaited', result, err
    if err:
      raise err
    return result


def ReadChunk(r):
  b = r.ReadByte()
  if b != 199:
    raise 'ReadChunk: bad magic'
  a = r.ReadByte()
  b = r.ReadByte()
  c = r.ReadByte()
  d = r.ReadByte()
  n = (a<<24) | (b<<16) | (c<<8) | d
  say 'ReadChunk', n
  z, eof = aphid.WrapRead(r, n)
  if eof:
    raise "got EOF"
  say 'ReadChunk', z
  return z

def Sum(*args):
  z = 0.0
  for a in args:
    z += float(a)
  return z

def SleepAndDouble(secs):
  say '<<<', secs
  time.Sleep(secs)
  say '>>>', secs
  return 2 * secs

def main(args):
  key = byt('abcdefghijklmnop')

  svr = Server2(':9999', 'key', key)
  svr.Register('Sum', Sum)
  svr.Register('SleepAndDouble', SleepAndDouble)
  go svr.Listen()

  time.Sleep(1.5)
  cli = Client2('localhost:9999', 'key', key)
  z = cli.Call('Sum', [100,200,300]).Wait()
  say z
  assert z == 600.0
  assert z == 600
  assert 600 == z

  d = {}
  for i in range(5):
    d[i] = cli.Call('SleepAndDouble', [i * 0.1])
    say i, d[i]

  for i in range(5):
    say 'GGGGETTING', i, d[i]
    z = d[i].Wait()
    say 'GGGGOT', i, d[i], z
    assert z == i * 0.2

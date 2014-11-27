from go import bufio, bytes, io
from go import net, sync, time
from go import crypto/rand

from go import github.com/strickyak/aphid

from . import dh, eval, gcm, keyring

SerialPrefix = mkbyt(12)  # Per Process nonce.
rand.Read(SerialPrefix)

SerialMutex = go_new(sync.Mutex)
SerialCounter = 100
def Serial():
  global SerialCounter
  SerialMutex.Lock()
  with defer SerialMutex.Unlock():
    SerialCounter += 1
    return (SerialPrefix, SerialCounter)

class Request:
  def __init__(proc, args):
    .proc = proc
    .args = args
    .serial = None
    .replyQ = aphid.NewChan(1)

CHUNK_MAGIC = 191
SHAKE_MAGIC = 222

def WriteChunk(w, data):
  n = len(data)
  head = byt([CHUNK_MAGIC, n>>24, n>>16, n>>8, n])
  buf = bytes.NewBuffer(head)
  buf.Write(data)
  io.Copy(w, buf)

def ReadChunk(r):
  head = mkbyt(5)
  io.ReadFull(r, head)
  must head[0] == CHUNK_MAGIC
  n = (head[1]<<24) | (head[2]<<16) | (head[3]<<8) | head[4]
  must n < (2 << 20)  # 2 Meg Max
  pay = mkbyt(n)
  io.ReadFull(r, pay)
  return pay

class Server:
  def __init__(hostport, ring):
    .hostport = hostport
    .ring = ring
    .procs = {}

  def Register(proc, fn):
    .procs[proc] = fn

  def ListenAndServe():
    .sock = net.Listen('tcp', .hostport)
    while True:
      conn = .sock.Accept()
      go ServerConn(self, conn).Run()

class ServerConn:
  def __init__(server, conn):
    .server = server
    .conn = conn

  def Handshake():
    msg = ReadChunk(.conn)
    magic, c, s = msg
    must magic == SHAKE_MAGIC
    mut = MutualKey(.server.ring, str(c), str(s))
    .sealer = gcm.Cipher(mut)

  def Run():
    .Handshake()
    .resultQ = aphid.NewChan(5)
    go .WriteActor()
    go .ReadActor()

  def WriteActor():
    while True:
      tup = .resultQ.Get()
      if tup is None:
        break
      serial, result, err = tup

      p = .sealer.Seal(rye_pickle( (serial, result, err) ), serial)
      WriteChunk(.conn, p)
    .conn.Close()

  def ReadActor():
    r = bufio.NewReader(.conn)
    with defer .resultQ.Put( None ):
      while True:
        toBreak = False
        try:
          dark = ReadChunk(r)
        except as ex:
          must str(ex) == 'EOF'
          toBreak = True
        if toBreak:
          break
        pay, ser = .sealer.Open(dark)
        serial, proc, args = rye_unpickle(pay)
        must ser == serial
        go .Execute(serial, proc, args)

  def Execute(serial, proc, args):
    result, err = None, None
    try:
      fn = .server.procs.get(proc)
      if not fn:
        raise 'rpc function not registered in Server', proc
      result = fn(*args)
    except as ex:
      err = ex
    .resultQ.Put( (serial, result, err) )


def MutualKey(ring, clientId, serverId):
  cli = ring[clientId]
  svr = ring[serverId]
  must cli.kind == 'dh'
  must svr.kind == 'dh'
  if cli.sec:
    secret = dh.DhSecret(cli.num, cli.name, dh.G3072, cli.pub, dh.Big(cli.sec))
    say 'C', secret.MutualKey(svr.pub)
    return secret.MutualKey(svr.pub)
  if svr.sec:
    secret = dh.DhSecret(svr.num, svr.name, dh.G3072, svr.pub, dh.Big(svr.sec))
    say 'S', secret.MutualKey(cli.pub)
    return secret.MutualKey(cli.pub)
  raise 'MISSING SECRET KEY'

class Client:
  def __init__(hostport, ring, clientId, serverId):
    .hostport = hostport
    .ring = ring
    .clientId = clientId
    .serverId = serverId
    .sealer = gcm.Cipher(MutualKey(ring, clientId, serverId))
    .requests = {}
    .inQ = aphid.NewChan(5)
    .conn = net.Dial('tcp', hostport)
    .Handshake()
    go .ReadActor()
    go .WriteActor()

  def Handshake():
    c, s = int(.clientId), int(.serverId)
    must c < 256
    must s < 256
    msg = byt([SHAKE_MAGIC, c, s])
    WriteChunk(.conn, msg)

  def WriteActor():
    while True:
      req = .inQ.Get()
      if req is None:
        break

      # Allocate a serial, and remember the request.
      req.serial = Serial()
      .requests[req.serial] = req

      pay = rye_pickle( (req.serial, req.proc, req.args) )
      dark = .sealer.Seal(pay, req.serial)
      WriteChunk(.conn, dark)

    .conn.Close()

  def ReadActor():
    r = bufio.NewReader(.conn)
    while True:
      # TODO -- when to stop.
      p = ReadChunk(r)
      pay, ser = .sealer.Open(p)
      serial, result, err = rye_unpickle(pay)
      must serial == ser # TODO
      .requests[serial].replyQ.Put( (result, err) )


  def Call(proc, args):
    req = Request(proc, args)
    .inQ.Put(req)
    return Promise(req.replyQ)

class Promise:
  def __init__(chan):
    .chan = chan

  def Wait():
    result, err = .chan.Get()
    if err:
      raise err
    return result


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

  svr = Server(':9999', ring=ring2)
  svr.Register('DemoSum', DemoSum)
  svr.Register('DemoSleepAndDouble', DemoSleepAndDouble)
  go svr.ListenAndServe()

  time.Sleep(100 * time.Millisecond)
  cli = Client('localhost:9999', ring1, '1', '2')
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

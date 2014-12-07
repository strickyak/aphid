from go import bufio, bytes, io
from go import net, sync, time
from go import crypto/rand

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
    .replyQ = rye_chan(1)

CHUNK_MAGIC = 191
SHAKE_MAGIC = 222

def WriteChunk(w, data):
  n = len(data)
  say w, n
  head = byt([CHUNK_MAGIC, n>>24, n>>16, n>>8, n])
  buf = bytes.NewBuffer(head)
  buf.Write(data)
  io.Copy(w, buf)

def ReadChunk(r):
  head = mkbyt(5)
  say 'read head'
  io.ReadFull(r, head)
  must head[0] == CHUNK_MAGIC
  n = (head[1]<<24) | (head[2]<<16) | (head[3]<<8) | head[4]
  must n < (2 << 20)  # 2 Meg Max
  pay = mkbyt(n)
  say 'read full', n
  io.ReadFull(r, pay)
  say 'read done'
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
    .resultQ = rye_chan(5)
    go .WriteActor()
    go .ReadActor()

  def WriteActor():
    while True:
      say 'get'
      tup = .resultQ.Get()
      say 'got', tup
      if tup is None:
        break
      serial, result, err = tup
      say serial, result, err

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
        say proc, args
        go .Execute(serial, proc, args)

  def Execute(serial, proc, args):
    result, err = None, None
    try:
      fn = .server.procs.get(proc)
      if not fn:
        raise 'rpc function not registered in Server', proc
      say fn
      result = fn(*args)
      say result
    except as ex:
      say ex
      err = ex
    .resultQ.Put( (serial, result, err) )
    say "put", ( (serial, result, err) )


def MutualKey(ring, clientId, serverId):
  say ring, clientId, serverId
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
    .inQ = rye_chan(5)
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
    say proc, args
    req = Request(proc, args)
    .inQ.Put(req)
    say 'RETURNING PROMISE', req.replyQ
    return Promise(req.replyQ)

class Promise:
  def __init__(chan):
    .chan = chan

  def Wait():
    say 'WAITING', .chan
    result, err = .chan.Get()
    say 'WAITED', result, err
    if err:
      raise err
    return result

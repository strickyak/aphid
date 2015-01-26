from go import bufio, bytes, io
from go import net, sync, time
from go import crypto/rand

from . import dh, sym, keyring

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

def AtMost(n, s):
  s = str(s)
  return s if len(s) < n else s[:n] + '...'

def ArgsSummary(args, kw):
  return str([AtMost(80, repr(x)) for x in args] + [(k, AtMost(80, repr(v))) for k, v in kw.items()])

class Request:
  def __init__(proc, args, kw):
    .proc = proc
    .args = args
    .kw = kw
    .serial = None
    .replyQ = rye_chan(1)

CHUNK_MAGIC = 191
SHAKE_MAGIC = 222

def WriteChunk(w, data):
  n = len(data)
  #say w, n
  head = byt([CHUNK_MAGIC, n>>24, n>>16, n>>8, n])
  buf = bytes.NewBuffer(head)
  buf.Write(data)
  io.Copy(w, buf)

def ReadChunk(r):
  head = mkbyt(5)
  #say 'read head'
  io.ReadFull(r, head)
  must head[0] == CHUNK_MAGIC
  n = (head[1]<<24) | (head[2]<<16) | (head[3]<<8) | head[4]
  must n < (100 << 20)  # 100 Meg Max
  pay = mkbyt(n)
  #say 'read full', n
  io.ReadFull(r, pay)
  #say 'read done'
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
    .sealer = sym.Cipher(mut)

  def Run():
    .Handshake()
    .resultQ = rye_chan(5)
    go .WriteActor()
    go .ReadActor()

  def WriteActor():
    while True:
      #say 'get'
      tup = .resultQ.Take()
      #say 'got', tup
      if tup is None:
        break
      serial, result, err = tup
      #say serial, result, err

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
        serial, proc, args, kw = rye_unpickle(pay)
        must ser == serial
        go .Execute(serial, proc, args, kw)

  def Execute(serial, proc, args, kw):
    say 'EXECUTE', proc, ArgsSummary(args, kw)
    result, err = None, None
    try:
      fn = .server.procs.get(proc)
      if not fn:
        raise 'rpc function not registered in Server', proc
      result = fn(*args, **kw)
    except as ex:
      say ex
      err = ex
    .resultQ.Put( (serial, result, err) )


def MutualKey(ring, clientId, serverId):
  say 'MutualKey', clientId, serverId
  cli = ring[clientId]
  svr = ring[serverId]
  must cli.kind == 'dh'
  must svr.kind == 'dh'
  if cli.sec:
    secret = dh.DhSecret(cli.num, cli.name, dh.GROUP, cli.pub, dh.Big(cli.sec))
    #say 'C', secret.MutualKey(svr.pub)
    return secret.MutualKey(svr.pub)
  if svr.sec:
    secret = dh.DhSecret(svr.num, svr.name, dh.GROUP, svr.pub, dh.Big(svr.sec))
    #say 'S', secret.MutualKey(cli.pub)
    return secret.MutualKey(cli.pub)
  raise 'MISSING SECRET KEY'

class Client:
  def __init__(hostport, ring, clientId, serverId):
    .hostport = hostport
    .ring = ring
    .clientId = clientId
    .serverId = serverId
    .sealer = sym.Cipher(MutualKey(ring, clientId, serverId))
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
      req = .inQ.Take()
      if req is None:
        break

      # Allocate a serial, and remember the request.
      req.serial = Serial()
      .requests[req.serial] = req

      pay = rye_pickle( (req.serial, req.proc, req.args, req.kw) )
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


  def Call(proc, *args, **kw):
    say 'CALLING', proc, ArgsSummary(args, kw)
    req = Request(proc, args, kw)
    .inQ.Put(req)
    return Promise(req.replyQ)

  def Close():
    try:
      .conn.Close()
    except as ex:
      say 'EXCEPTION', ex


class Promise:
  def __init__(chan):
    .chan = chan

  def Wait():
    result, err = .chan.Take()
    say AtMost(80, result), AtMost(80, err)
    if err:
      raise 'PromiseWaitError', err
    return result

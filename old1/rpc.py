from go import bufio, bytes, io
from go import net, sync, time
from go import crypto/rand

from go import github.com/strickyak/aphid

from . import eval, gcm, keyring

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
  def __init__(hostport, keyname, key):
    .hostport = hostport
    .keyname = keyname
    .procs = {}
    .sealer = gcm.Cipher(key)
    .outQ = aphid.NewChan(5)
    go .WriteActor()

  def ListenAndServe():
    .sock = net.Listen('tcp', .hostport)
    while True:
      conn = .sock.Accept()
      go .DoRead(conn)

  def WriteActor():
    while True:
      tup = .outQ.Get()
      if tup is None:
        break
      conn, serial, result, err = tup

      p = .sealer.Seal(rye_pickle( (serial, result, err) ), serial)
      WriteChunk(conn, p)
    .conn.Close()

  def DoRead(conn):
    r = bufio.NewReader(conn)
    with defer conn.Close():
      while True:
        try:
          dark = ReadChunk(r)
        except as ex:
          must str(ex) == 'EOF'
          return
        pay, ser = .sealer.Open(dark)
        unp = rye_unpickle(pay)
        serial, proc, args = unp
        must ser == serial
        go .Execute(conn, serial, proc, args)

  def Execute(conn, serial, proc, args):
    result, err = None, None
    try:
      fn = .procs.get(proc)
      if not fn:
        raise 'rpc function not registered in Server', proc
      result = fn(*args)
    except as ex:
      err = ex
    .outQ.Put( (conn, serial, result, err) )

  def Register(proc, fn):
    .procs[proc] = fn


class Client:
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
  key = byt('abcdefghijklmnop')

  svr = Server(':9999', 'key', key)
  svr.Register('DemoSum', DemoSum)
  svr.Register('DemoSleepAndDouble', DemoSleepAndDouble)
  go svr.ListenAndServe()

  time.Sleep(100 * time.Millisecond)
  cli = Client('localhost:9999', 'key', key)
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

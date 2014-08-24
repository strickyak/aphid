from go import bufio
from go import net
from go import time
from go import crypto/aes
#//from go import crypto/cipher

from go import github.com/strickyak/aphid
from . import eval

SerialCounter = 101
def Serial():
  global SerialCounter
  SerialCounter += 1
  return SerialCounter

class Request:
  def __init__(proc, args):
    .proc = proc
    .args = args
    .serial = None
    .replyQ = aphid.NewChan(1)

def WriteChunk(w, data):
  data = byt(data)
  bb = aphid.NewBuffer()
  bb.WriteChunk(data)
  w.Write(bb.Bytes())

class Server2:
  def __init__(hostport, keyname, key):
    .hostport = hostport
    .keyname = keyname
    .key = key
    .block = aes.NewCipher(key)
    .outQ = aphid.NewChan(5)
    go .WriteActor()
    .Listen()

  def Listen():
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

      say serial, result, err
      p = pickle( (serial, result, err) )
      say 'pickle', p
      say '... pickle', unpickle(p)
      WriteChunk(conn, p)
    .sock.Close()

  def DoRead(conn):
    # TODO -- when to stop.
    r = bufio.NewReader(conn)
    p = ReadChunk(r)
    say 'DoRead', p
    say 'DoRead', len(p)
    unp = unpickle(p)
    say 'DoRead', unp
    serial, proc, args = unp
    say 'DoRead', serial, proc, args
    go .Execute(conn, serial, proc, args)

  def Execute(conn, serial, proc, args):
    # Use repr for standin.
    result, err = repr( (proc, args) ), None
    .outQ.Put( (conn, serial, result, err) )


class Client2:
  def __init__(hostport, keyname, key):
    .hostport = hostport
    .keyname = keyname
    .key = key
    .block = aes.NewCipher(key)
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
      p = pickle( (req.serial, req.proc, req.args) )
      say 'pickle WA WC', p
      say 'pickle WA WC', len(p)
      say '... pickle WA WC', unpickle(p)
      WriteChunk(.conn, p)

    .conn.Close()

  def ReadActor():
    r = bufio.NewReader(.conn)
    while True:
      # TODO -- when to stop.
      p = ReadChunk(r)
      say 'pickle RC', p
      serial, result, err = unpickle(p)
      .requests[serial].replyQ.Put( (result, err) )


  def Call(proc, args):
    req = Request(proc, args)
    .inQ.Put(req)
    reply = req.replyQ.Get()
    say reply
    result, err = reply
    say result, err
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
  say n
  z, eof = aphid.WrapRead(r, n)
  if eof:
    raise "got EOF"
  say z
  return z

def main(args):
  key = byt('abcdefghijklmnop')
  go Server2(':9999', 'key', key)
  time.Sleep(5.5)
  c = Client2('localhost:9999', 'key', key)
  z = c.Call('foo', [100,200,300])
  say z
  assert z == "(\"foo\", [100, 200, 300])"
  assert eval.Eval(z) == ('foo', [100,200,300])

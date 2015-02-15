from go import os, time
from go import path/filepath as F

from . import A, bundle, flag, hanger, keyring, pubsub, rpc2

KEYNAME = byt('default')
KEY = byt('ABCDEFGHabcdefgh')

TheHanger = hanger.Hanger()

class RemoteBase:
  def __init__(cli, id):
    .cli = cli
    .id = id
    .seq = 0
  def Advance():
    .seq += 1

class RemoteReader(RemoteBase):
  def __init__(cli, id):
    super.__init__(cli, id)
  def ReadChunk(n):
    say n
    with defer .Advance():
      bb = .cli.RInvoke(.id, .seq, 'ReadChunk', n).Wait()
    say len(bb), n
    return bb
  def Close():
    say 'Close'
    with defer .Advance():
      .cli.RInvoke(.id, .seq, 'Close').Wait()
    say 'Closeed'
native:
  `
    func (self *C_RemoteReader) Read(p []byte) (n int, err error) {
      plen := len(p)
      var x P

      func() {
        defer func() {
          r := recover()
          if r != nil {
            println(fmt.Sprintf("RemoteReader::Close: r == %T %#v", r, r))
            err = NewErrorOrEOF(r)
            println(fmt.Sprintf("RemoteReader::Close: err == %T %#v", err, err))
          }
          return
        }()
        x = self.M_1_ReadChunk(Mkint(plen))
      }()

      if err == nil {
        xb := x.Bytes()
        copy(p, xb)
        n = x.Len()
      }
      return
    }
    func (self *C_RemoteReader) Close(p []byte) (err error) {
      self.M_0_Close()
      return nil
    }
  `

class RemoteWriter(RemoteBase):
  def __init__(cli, id):
    super.__init__(cli, id)
  def WriteChunk(bb):
    say len(bb)
    with defer .Advance():
      .cli.RInvoke(.id, .seq, 'WriteChunk', bb).Wait()
      say 'did .cli.RInvoke', .id, .seq
  def Close():
    with defer .Advance():
      .cli.RInvoke(.id, .seq, 'Close').Wait()
native:
  `
    func (self *C_RemoteWriter) Write(p []byte) (n int, err error) {
      plen := len(p)
      self.M_1_WriteChunk(MkByt(p))
      return plen, nil
    }
    func (self *C_RemoteWriter) Close(p []byte) (err error) {
      self.M_0_Close()
      return nil
    }
  `

class RBundleClient(rpc2.Client):
  def __init__(hostport, ring, clientId, serverId):
    super(hostport, ring, clientId, serverId)
    .me = clientId

  def RPing():
    return .Call("XPing").Wait()

  def RInvoke(id, seq, msg, *args, **kw):
    return .Call("XInvoke", id, seq, msg, *args, **kw)

  def OpenRemoteReader(bund, path, pw):
    id = .RMakeChunkReader(bund=bund, path=path, pw=pw).Wait()
    say id
    z = RemoteReader(cli=self, id=id)
    say z
    return z

  def OpenRemoteWriter(bund, path, pw):
    id = .RMakeChunkWriter(bund=bund, path=path, pw=pw).Wait()
    say id
    z = RemoteWriter(cli=self, id=id)
    say z
    return z

  def RMakeChunkReader(bund, path, pw):
    return .Call('XMakeChunkReader', bund=bund, path=path, pw=pw)

  def RMakeChunkWriter(bund, path, pw):
    return .Call('XMakeChunkWriter', bund=bund, path=path, pw=pw)

  def RStat3(bund, path, pw=None):
    return .Call("XStat3", bund=bund, path=path, pw=pw).Wait()

  def RList4(bund, path, pw=None):
    return .Call("XList4", bund=bund, path=path, pw=pw).Wait()

  def RReadFile(bund, path, rev=None, pw=None):
    return .Call("XReadFile", bund=bund, path=path, rev=rev, pw=pw).Wait()

  def RReadRawFile(bund, rawpath):
    return .Call("XReadRawFile", bund=bund, rawpath=rawpath).Wait()

  def RWriteFile(bund, path, data, mtime=-1, rev=None, slave=None, pw=None):
    return .Call("XWriteFile", bund, path, data, mtime, rev, slave, pw=pw).Wait()

  def RWriteRawFile(bund, rawpath, data):
    return .Call("XWriteRawFile", bund, rawpath=rawpath, data=data).Wait()

  def RPublish(origin, key1, key2, props):
    return .Call("XPublish", origin=origin, key1=key1, key2=key2, props=props)


class RBundleServer(rpc2.Server):
  def __init__(aphid, hostport, ring):
    super(hostport, ring)
    .aphid = aphid
    .bus = aphid.bus
    .bundles = aphid.bundles
    .Register('XPing', .SPing)
    .Register('XInvoke', .SInvoke)
    .Register('XMakeChunkReader', .SMakeChunkReader)
    .Register('XMakeChunkWriter', .SMakeChunkWriter)
    .Register('XStat3', .SStat3)
    .Register('XList4', .SList4)
    .Register('XReadFile', .SReadFile)
    .Register('XReadRawFile', .SReadRawFile)
    .Register('XWriteFile', .SWriteFile)
    .Register('XWriteRawFile', .SWriteRawFile)
    .Register('XPublish', .SPublish)

  def SPing():
    return A.NowNanos()

  def SInvoke(id, seq, msg, *args, **kw):
    say seq, msg, args, kw
    z = TheHanger.Invoke(id, seq, msg, *args, **kw)
    say z
    return z

  def SMakeChunkReader(bund, path, pw):
    say bund, path, pw
    cr = .bundles[bund].MakeChunkReader(path=path, pw=pw)
    say cr
    id_r = TheHanger.Hang(cr)
    say id_r
    return id_r

  def SMakeChunkWriter(bund, path, pw):
    say bund, path, pw
    cw = .bundles[bund].MakeChunkWriter(path=path, pw=pw)
    say cw
    id_w = TheHanger.Hang(cw)
    say id_w
    return id_w

  def SStat3(bund, path, pw=None):
    say bund, path
    return .bundles[bund].Stat3(path=path, pw=pw)

  def SList4(bund, path, pw=None):
    say bund, path
    return list(.bundles[bund].List4(path=path, pw=pw))

  def SReadFile(bund, path, rev, pw=None):
    say bund, path, rev
    return .bundles[bund].ReadFile(path=path, rev=rev, pw=pw)

  def SReadRawFile(bund, rawpath):
    say bund, rawpath
    return .bundles[bund].ReadRawFile(rawpath=rawpath)

  def SWriteFile(bund, path, data, mtime, rev=None, slave=None, pw=None):
    say bund, path, mtime, len(data), rev, slave
    return .bundles[bund].WriteFile(path=path, data=data, mtime=mtime, rev=rev, slave=slave, pw=pw)

  def SWriteRawFile(bund, rawpath, data):
    say bund, rawpath, len(data)
    return .bundles[bund].WriteRawFile(rawpath=rawpath, data=data)

  def SPublish(origin, key1, key2, props):
    say origin, key1, key2, props
    must origin
    must key1
    thing = pubsub.Thing(origin=origin, key1=key1, key2=key2, props=props)
    .bus.Publish(thing)

pass

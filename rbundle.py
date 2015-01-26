from go import os, time
from go import path/filepath as F

from . import A, bundle, flag, keyring, pubsub, rpc2

KEYNAME = byt('default')
KEY = byt('ABCDEFGHabcdefgh')

class RBundleClient(rpc2.Client):
  def __init__(hostport, ring, clientId, serverId):
    super(hostport, ring, clientId, serverId)
    .me = clientId

  def Ping():
    return .Call("Ping").Wait()

  def RStat3(bund, path):
    return .Call("RStat3", bund=bund, path=path).Wait()

  def RList4(bund, path):
    return .Call("RList4", bund=bund, path=path).Wait()

  def RReadFile(bund, path, rev=None):
    return .Call("RReadFile", bund=bund, path=path, rev=rev).Wait()

  def RWriteFile(bund, path, data, mtime=-1, rev=None, slave=None):
    return .Call("RWriteFile", bund, path, data, mtime, rev, slave).Wait()

  def RPublish(origin, key1, key2, props):
    return .Call("RPublish", origin=origin, key1=key1, key2=key2, props=props)


class RBundleServer(rpc2.Server):
  def __init__(aphid, hostport, ring):
    super(hostport, ring)
    .aphid = aphid
    .bus = aphid.bus
    .bundles = aphid.bundles
    .Register('Ping', .Ping)
    .Register('RStat3', .RStat3)
    .Register('RList4', .RList4)
    .Register('RReadFile', .RReadFile)
    .Register('RWriteFile', .RWriteFile)
    .Register('RPublish', .RPublish)

  def Ping():
    return A.NowNanos()

  def RStat3(bund, path):
    say bund, path
    return .bundles[bund].Stat3(path=path)

  def RList4(bund, path):
    say bund, path
    return list(.bundles[bund].List4(path=path))

  def RReadFile(bund, path, rev):
    say bund, path, rev
    return .bundles[bund].ReadFile(path=path, rev=rev)

  def RWriteFile(bund, path, data, mtime, rev=None, slave=None):
    say bund, path, mtime, len(data), rev, slave
    return .bundles[bund].WriteFile(path=path, data=data, mtime=mtime, rev=rev, slave=slave)

  def RPublish(origin, key1, key2, props):
    say origin, key1, key2, props
    must origin
    must key1
    thing = pubsub.Thing(origin=origin, key1=key1, key2=key2, props=props)
    .bus.Publish(thing)

pass

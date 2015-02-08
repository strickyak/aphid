from go import os, time
from go import path/filepath as F

from . import A, bundle, flag, keyring, pubsub, rpc2

KEYNAME = byt('default')
KEY = byt('ABCDEFGHabcdefgh')

class RBundleClient(rpc2.Client):
  def __init__(hostport, ring, clientId, serverId):
    super(hostport, ring, clientId, serverId)
    .me = clientId

  def RPing():
    return .Call("XPing").Wait()

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
    .Register('XStat3', .SStat3)
    .Register('XList4', .SList4)
    .Register('XReadFile', .SReadFile)
    .Register('XReadRawFile', .SReadRawFile)
    .Register('XWriteFile', .SWriteFile)
    .Register('XWriteRawFile', .SWriteRawFile)
    .Register('XPublish', .SPublish)

  def SPing():
    return A.NowNanos()

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

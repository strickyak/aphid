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
    return .Call("Ping", []).Wait()

  def RStat3(bund, path):
    return .Call("RStat3", [bund, path]).Wait()

  def RList4(bund, path):
    return .Call("RList4", [bund, path]).Wait()

  def RReadFile(bund, path, rev=None):
    return .Call("RReadFile", [bund, path, rev]).Wait()

  def RWriteFile(bund, path, data, mtime=-1, rev=None, slave=None):
    return .Call("RWriteFile", [bund, path, data, mtime, rev, slave]).Wait()

  def RPublish(origin, key1, key2, props):
    return .Call("RPublish", origin, key1, key2, props)

def Ping():
  return A.NowNanos()

def RStat3(bund, path):
  say bund, path
  return bundle.Bundles[bund].Stat3(path)

def RList4(bund, path):
  say bund, path
  return list(bundle.Bundles[bund].List4(path))

def RReadFile(bund, path, rev):
  say bund, path, rev
  return bundle.Bundles[bund].ReadFile(path, rev)

def RWriteFile(bund, path, data, mtime, rev=None, slave=None):
  say bund, path, mtime, len(data), rev, slave
  return bundle.Bundles[bund].WriteFile(path, data, mtime, rev=rev, slave=slave)

def RPublish(origin, key1, key2, props):
  say origin, key1, key2, props
  must origin
  must key1
  thing = pubsub.Thing(origin=origin, key1=key1, key2=key2, props=props)
  pubsub.Publish(thing)


class RBundleServer(rpc2.Server):
  def __init__(hostport, ring):
    super(hostport, ring)
    .Register('Ping', Ping)
    .Register('RStat3', RStat3)
    .Register('RList4', RList4)
    .Register('RReadFile', RReadFile)
    .Register('RWriteFile', RWriteFile)
    .Register('RPublish', RPublish)

BIND = flag.String('rbundle_bind', 'localhost:8081', 'Port to listen on')
RING = flag.String('rbundle_keyring', 'test.ring', 'Test Keyring')

def main(args):
  args = flag.Munch(args)
  keyring.Load(RING.X, keyring.Ring)

  if args:
    cli = RBundleClient(BIND.X, keyring.Ring, '91', '92')
    cmd = args.pop(0)
    if cmd == 'list':
      bund = args.pop(0)
      path = args.pop(0)
      say cli.RList4(bund, path)
  else:
    for bname, _ in flag.Triples.get('bundle', {}).items():
      bundir = F.Join('.', 'b.%s' % bname)
      bundle.Bundles[bname] = bundle.Bundle(bname, bundir=bundir)
    server = RBundleServer(BIND.X, keyring.Ring)
    server.ListenAndServe()

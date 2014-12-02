from go import os
from go import path/filepath

from . import A, bundle, flag, keyring, rpc2

KEYNAME = byt('default')
KEY = byt('ABCDEFGHabcdefgh')

class RBundleClient(rpc2.Client):
  def __init__(hostport, ring, clientId, serverId):
    super(hostport, ring, clientId, serverId)

  def RStat3(bund, path):
    return .Call("RStat3", [bund, path]).Wait()

  def RList4(bund, path):
    say bund, path
    return .Call("RList4", [bund, path]).Wait()

  def RReadFile(bund, path):
    return .Call("RReadFile", [bund, path]).Wait()

  def RWriteFile(bund, path, data, mtime=-1):
    return .Call("RWriteFile", [bund, path, data, mtime]).Wait()

def RStat3(bund, path):
  return bundle.Bundles[bund].Stat3(path)

def RList4(bund, path):
  say bund, path
  say bundle.Bundles
  return list(bundle.Bundles[bund].List4(path))

def RReadFile(bund, path):
  return bundle.Bundles[bund].ReadFile(path)

def RWriteFile(bund, path, data, mtime):
  return bundle.Bundles[bund].WriteFile(path, data, mtime)

class RBundleServer(rpc2.Server):
  def __init__(hostport, ring):
    super(hostport, ring)
    .Register('RStat3', RStat3)
    .Register('RList4', RList4)
    .Register('RReadFile', RReadFile)
    .Register('RWriteFile', RWriteFile)

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
    for k, v in flag.Triples.get('bundle', {}).items():
      bundle.LoadBundle(k)
    server = RBundleServer(BIND.X, keyring.Ring)
    server.ListenAndServe()

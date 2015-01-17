from go import time
from . import A, bundle, flag, keyring, pubsub, rbundle

ALL = flag.String('all', '', 'List of all nodes')
ME = flag.String('me', '', 'My id')

WATCHDOG_PERIOD = 2

def Now():
  return time.Now().Unix()

def Sleep(secs):
  time.Sleep(secs * time.Second)

Others = {}

def Start():
  say ALL.X, ALL.X.split(',')
  for w in ALL.X.split(','):
    say w
    id, where = w.split('=')
    if id != ME.X:
      node = Node(id, where)
      go node.Watchdog()
      Others[id] = node

class Node:
  def __init__(id, where):
    say "NEW NODE", id, where
    .id = id
    .where = where
    .lasttime = Now()

    hostport, ring, clientId, serverId = .where, keyring.Ring, ME.X, .id
    .client = rbundle.RBundleClient(hostport, ring, clientId, serverId)

  def Watchdog():
    # Stay in this loop until watchdog fails to ping.
    while True:
      Sleep(WATCHDOG_PERIOD / 2.0)
      say 'go .PingAndUpdate()'
      go .PingAndUpdate()
      Sleep(WATCHDOG_PERIOD / 2.0)
      if .lasttime < Now() - WATCHDOG_PERIOD:
            break

    # Shutdown this Node Connection, and start another.
    newnode = Node(.id, .where)
    go newnode.Watchdog()
    Others[.id] = newnode

    try:
      .client.Close()
    except as ex:
      say 'Watchdog Shutdown Exception:', ex

  def PingAndUpdate():
    try:
      then = time.Now().UnixNano()
      say .id, .where, then
      t = .client.Ping()
      now = time.Now().UnixNano()
      say .id, .where, then, t, now, (now-t), (now-then)
      say float(now-t) / float(1.0e6), float(now-then) / float(1.0e6)
      .lasttime = Now()
    except as ex:
      say 'EXCEPTION', ex

def BestEffortCallAllOthers(proc, args):
  for name, cli in Others:
    go cli.Call(proc, args)

def WriteFileRevSyncronizerFunc(thing):
  if thing.origin is None:
    # Originated locally, so send it to remotes.
    BestEffortCallAllOthers('RPublish', thing)
    return

  # Originated from elsewhere.
  b = bundle.Bundles.get(thing.key1)
  if not b:
    A.Err('Bundle %q NOT FOUND for WriteFileRevSyncronizerFunc, thing=%v', thing.key1, thing)
    return

  p = thing.props
  ppath, psize, psum, prev, pmtime = p['path'], p['size'], p['csum'], p['rev'], p['mtime']
  revs = b.ListRevs(ppath)
  if prev in revs:
    return  # Already got it.

  remote = Others.get(thing.origin)
  if not remote:
    A.Err('No connection to Origin: %q', thing.origin)

  data = remote.ReadFileRev(ppath, rev=prev)
  b.WriteFile(ppath, data, mtime=pmtime, rev=prev, slave=thing)

def StartSyncronizer():
  sub = pubsub.Sub(key1='WriteFileRev', re2=None, fn=WriteFileRevSyncronizerFunc)
  pubsub.Subscribe(sub)

def main(args):
  args = flag.Munch(args)
  keyring.Load(rbundle.RING.X, keyring.Ring)
  Start()
  Sleep(3600 * 24 * 365 * 10)  # 10 years is a long time.

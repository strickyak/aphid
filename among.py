from go import time
from . import flag, keyring, rbundle

ALL = flag.String('among_all', '', 'List of all nodes')
MY_ID = flag.String('among_my_id', '', 'My id')

WATCHDOG_PERIOD = 15

def Now():
  return time.Now().Unix()

def Sleep(secs):
  time.Sleep(secs * time.Second)

Others = {}

def Start():
  say ALL.X, ALL.X.split(',')
  for w in ALL.X.split(','):
    say w
    id, where = w.split('/')
    if id != MY_ID.X:
      p = Node(id, where)
      go p.Watchdog()
      Others[where] = p

class Node:
  def __init__(id, where):
    say "NEW NODE", id, where
    .id = id
    .where = where
    .lasttime = Now()

    hostport, ring, clientId, serverId = .where, keyring.Ring, MY_ID.X, .id
    .client = rbundle.RBundleClient(hostport, ring, clientId, serverId)

  def Watchdog():
    while True:
      Sleep(WATCHDOG_PERIOD / 2.0)
      say 'go .PingAndUpdate()'
      go .PingAndUpdate()
      Sleep(WATCHDOG_PERIOD / 2.0)
      if .lasttime < Now() - WATCHDOG_PERIOD:
        # Shutdown this Node Connection, and start another.
        p = Node(.id, .where)
        go p.Watchdog()
        Others[.where] = p
        break

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

def main(args):
  args = flag.Munch(args)
  keyring.Load(rbundle.RING.X, keyring.Ring)
  Start()
  Sleep(3600 * 24 * 365 * 10)  # 10 years is a long time.

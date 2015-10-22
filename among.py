from go import io, log, math/rand, regexp, time
from . import A, bundle, keyring, pubsub, rbundle

WATCHDOG_PERIOD = 300.0
MAX_BACKOFF = 120

class Among:
  def __init__(aphid, my_id, peer_map):
    my_id = str(my_id)
    .aphid = aphid
    .ring = .aphid.ring
    .bus = .aphid.bus
    must type(peer_map) == dict
    must my_id in peer_map
    .my_id = my_id
    .peer_map = peer_map
    .conn_map = {}
    say 'CTOR Among', .my_id, .peer_map

  def Start():
    for peer_id, peer_loc in .peer_map.items():
      if peer_id != .my_id:
        go .Connect(peer_id, peer_loc)

  def Connect(peer_id, peer_loc):
    say 'Connect <<<', .my_id, peer_id, peer_loc
    backoff = 1.0
    while True:
      try:
        conn = Conn(self, peer_id, peer_loc)
        .conn_map[peer_id] = conn
        say 'Connect >>>>>>>>>>>>>>', .my_id, peer_id, peer_loc
        go conn.Watchdog()
        return
      except:
        pass
      say 'Connect === Backoff', .my_id, peer_id, peer_loc, backoff
      A.Sleep(backoff)
      backoff = min(float(backoff), MAX_BACKOFF/2.0)
      backoff *= rand.Float64() + 1.0

  def BestEffortCallAllOthers(proc_name, *args, **kw):
    say proc_name, args, kw
    for name, conn in .conn_map.items():
      say name, conn
      go conn.client.Call(proc_name, *args, **kw)

  def WriteFileSyncronizerFunc(thing):
    say thing
    assert thing.key1 == 'WriteFile'
    if thing.origin is None:
      # Originated locally, so send it to remotes.
      .BestEffortCallAllOthers('XPublish', .my_id, thing.key1, thing.key2, thing.props)
      return

    say thing.origin
    if thing.origin == .my_id:
      say 'MON RAW: Do not send to ourself', .my_id
      return

    # Originated from elsewhere.
    bname = thing.key2
    say bname
    b = .aphid.bundles.get(bname)
    if not b:
      log.Printf('Bundle %q NOT FOUND for WriteFileSyncronizerFunc, thing=%v', bname, thing)
      return

    say thing.props
    p = thing.props
    rawpath = p['rawpath']
    say rawpath

    remote = .conn_map.get(thing.origin)
    if not remote:
      log.Printf('No connection to Origin: %q', thing.origin)

    say 'MON RAW: ', .my_id, thing.origin, b.bundir
    say 'MON RAW: remote.client.RemoteOpen', (b.bname, rawpath, None, True)
    r = remote.client.RemoteOpen(b.bname, rawpath, pw=None, raw=True)
    say 'MON RAW: RawChunkWriter', (b.bname, rawpath)
    w = bundle.RawChunkWriter(bund=b, path=rawpath, mtime=None)
    say 'MON RAW: bundle.CopyChunks'
    bundle.CopyChunks(w, r)
    say 'MON RAW: w.Close'
    w.Close()
    say 'MON RAW: r.Close'
    r.Close()


  def StartSyncronizer():
    sub = pubsub.Sub(key1='WriteFile', re2=None, fn=.WriteFileSyncronizerFunc)
    .bus.Subscribe(sub)

class Conn:
  def __init__(among, peer_id, peer_where):
    say "NEW CONN", peer_id, peer_where
    .among = among
    .peer_id = peer_id
    .peer_where = peer_where
    .lasttime = A.NowSecs()

    hostport, ring, clientId, serverId = .peer_where, among.ring, .among.my_id, .peer_id
    say hostport, clientId, serverId
    .client = rbundle.RBundleClient(hostport, ring, clientId, serverId)

  def Watchdog():
    # Stay in this loop until watchdog fails to ping.
    while True:
      A.Sleep(WATCHDOG_PERIOD / 2)
      say 'go .PingAndUpdate()'
      go .PingAndUpdate()
      A.Sleep(WATCHDOG_PERIOD / 2)
      if .lasttime < A.NowSecs() - WATCHDOG_PERIOD:
            break

    # Shutdown this Connection, and start another.
    new_conn = Conn(.among, .peer_id, .peer_where)
    go new_conn.Watchdog()
    .among.conn_map[.peer_id] = new_conn

    try:
      .client.Close()
    except as ex:
      say 'Watchdog Shutdown Exception:', ex

  def PingAndUpdate():
    try:
      then = A.NowNanos()
      say .peer_id, .peer_where, then
      t = .client.RPing()
      now = A.NowNanos()
      say .peer_id, .peer_where, then, t, now, (now-t), (now-then)
      say float(now-t) / float(1.0e6), float(now-then) / float(1.0e6)
      .lasttime = A.NowSecs()
    except as ex:
      say 'EXCEPTION', ex

pass

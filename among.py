from go import regexp, time
from . import A, bundle, pubsub, rbundle

WATCHDOG_PERIOD = 10

class Among:
  def __init__(my_id, all_ids_map, ring):
    must type(all_ids_map) == dict
    must my_id in all_ids_map
    .my_id = my_id
    .all_ids_map = all_ids_map
    .ring = ring
    .conn_map = {}

  def Start():
    for peer_id, peer_loc in .all_ids_map.items():
      if peer_id != .my_id:
        go .Connect(peer_id, peer_loc)

  def Connect(peer_id, peer_loc):
    while True:
      try:
        conn = Conn(self, peer_id, peer_loc)
        .conn_map[peer_id] = conn
        go conn.Watchdog()
        return
      except:
        pass
      A.Sleep(WATCHDOG_PERIOD / 4)

  def BestEffortCallAllOthers(proc_name, arg_list):
    say proc_name, arg_list
    for name, conn in .conn_map.items():
      say name, conn
      go conn.client.Call(proc_name, arg_list)

  def WriteFileRevSyncronizerFunc(thing):
    say thing
    assert thing.key1 == 'WriteFileRev'
    if thing.origin is None:
      # Originated locally, so send it to remotes.
      .BestEffortCallAllOthers(proc_name='RPublish', arg_list=[
          .my_id, thing.key1, thing.key2, thing.props])
      return

    # Originated from elsewhere.
    say thing.key2
    b = bundle.Bundles.get(thing.key2)
    if not b:
      A.Err('Bundle %q NOT FOUND for WriteFileRevSyncronizerFunc, thing=%v' % (thing.key2, thing))
      return

    p = thing.props
    say p
    ppath, psize, psum, prev, pmtime = p['path'], p['size'], p['csum'], p['rev'], p['mtime']
    say ppath, psize, psum, prev, pmtime
    say ppath
    revs = []
    try:
      revs = b.ListRevs(ppath)
    except:
      pass
    if prev in revs:
      return  # Already got it.

    remote = .conn_map.get(thing.origin)
    if not remote:
      A.Err('No connection to Origin: %q', thing.origin)

    try:
      say ppath

      say '@@@@ RReadFile', b.bname, ppath, prev
      data = remote.client.RReadFile(b.bname, ppath, rev=prev)
      say '@@@@ RReadFile', len(data)

      say '@@@@ WriteFile', ppath, len(data), pmtime, prev
      b.WriteFile(ppath, data, mtime=pmtime, rev=prev, slave=thing)
      say '@@@@ WriteFile', ppath, len(data)

    except as ex:
      say '@@@@@@@@@ EXCEPT:', ex
      raise 'Exception In WriteFileRevSyncronizerFunc', ex

  def StartSyncronizer():
    sub = pubsub.Sub(key1='WriteFileRev', re2=None, fn=.WriteFileRevSyncronizerFunc)
    pubsub.Subscribe(sub)

class Conn:
  def __init__(among, peer_id, peer_where):
    say "NEW CONN", peer_id, peer_where
    .among = among
    .peer_id = peer_id
    .peer_where = peer_where
    .lasttime = A.NowSecs()

    hostport, ring, clientId, serverId = .peer_where, among.ring, .among.my_id, .peer_id
    .client = rbundle.RBundleClient(hostport, ring, clientId, serverId)

  def Watchdog():
    # Stay in this loop until watchdog fails to ping.
    while True:
      A.Sleep(WATCHDOG_PERIOD / 2.0)
      say 'go .PingAndUpdate()'
      go .PingAndUpdate()
      A.Sleep(WATCHDOG_PERIOD / 2.0)
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
      t = .client.Ping()
      now = A.NowNanos()
      say .peer_id, .peer_where, then, t, now, (now-t), (now-then)
      say float(now-t) / float(1.0e6), float(now-then) / float(1.0e6)
      .lasttime = A.NowSecs()
    except as ex:
      say 'EXCEPTION', ex

pass

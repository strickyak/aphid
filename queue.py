from go import sync 

class BigQueue:
  def __init__():
    .d = {}
    .next_in = 1
    .next_out = 1
    .mutex = go_new(sync.Mutex)
    .chan = None

  def Send(x):
    .mutex.Lock()
    with defer .mutex.Unlock():
      .d[.next_in] = x
      .next_in += 1
      if .chan:
        .chan.Send(True)
        .chan = None
    
  def Recv():
    """There must be only one Recv task."""
    while True:
      .mutex.Lock()
      with defer .mutex.Unlock():
        if .next_out < .next_in:
          z = .d[.next_out]
          .next_out += 1
          return z
        ch = None
        if not .chan:
          ch = rye_chan(1)
          .chan = ch
      if ch:
        ch.Recv()
   
class Actor:
  """Single-threaded Actor."""
  def __init__():
    .done = rye_chan(1)
    .q = BigQueue()
    go ._Run()

  def _Run():
    while True:
      fn = .q.Recv()
      if fn is None:
        .done.Send(True)
        return
      fn()

  def Do(fn):
    """Enqueue fn to be run by actor.  Use None to stop."""
    .q.Send(fn)

  def Wait():
    """Wait for a None to be processed."""
    .done.Recv()

pass

"""You can hang an object on a Hanger, with a key name.
   Use it within a minute, or it will be .Dispose()d.
"""
from go import sync, time
from "github.com/strickyak/rye/contrib" import sema
import A

TIMEOUT = 60

class Hung:
  def __init__(hanger, id, x):
    .mu = go_new(sync.Mutex)
    .hanger = hanger
    .id = id
    .x = x
    .seq = 0
    .Touch()
    go .GC()

  def Touch():
    .ts = time.Now().Unix()

  def GC():
    while True:
      A.Sleep(TIMEOUT / 2.0)
      .mu.Lock()
      with defer .mu.Unlock():
        now = time.Now().Unix()
        if now > .ts + TIMEOUT:
          # Expired.
          x = .x
          .x = None
          del .hanger.d[.id]
          try:
            x.Dispose()
          except:
            pass
          return

  def Invoke(seq, msg, *args, **kw):
    .mu.Lock()
    with defer .mu.Unlock():
      must seq == .seq
      .seq += 1
      fn = getattr(.x, msg)
      must callable(fn), fn
      z = fn(*args, **kw)
      .Touch()
      return z

class Hanger:
  def __init__():
    .d = {}
    .serial = sema.Serial()

  def Hang(obj):
    "Hang the object on the hanger, and get an id for it."
    id = .serial.Recv()
    .d[id] = Hung(self, id, obj)
    return id

  def Invoke(id, seq, msg, *args, **kw):
    "Invoke msg on object id.  seq starts at 0, and must increment."
    say id, seq, msg, args, kw
    hung = .d[id]
    z = hung.Invoke(seq, msg, *args, **kw)
    say z
    return z

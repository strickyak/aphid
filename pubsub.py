from go import regexp, sync
from . import A

class Bus:
  def __init__(aphid):
    .aphid = aphid
    .subs = {}
    .mu = go_new(sync.Mutex)

  def Subscribe(sub):
    .mu.Lock()
    with defer .mu.Unlock():
      if sub.key1 not in .subs:
        .subs[sub.key1] = {}
      .subs[sub.key1][str(sub)] = sub

  def Unsubscribe(sub):
    .mu.Lock()
    with defer .mu.Unlock():
      del .subs[sub.key1][str(sub)]

  def Publish(thing):
    say thing
    .mu.Lock()
    with defer .mu.Unlock():
      d = .subs.get(thing.key1)
      if d:
        say d
        for sub in d.values():
          if not sub.re2 or sub.re2.FindString(thing.key2):
            say sub
            go sub.fn(thing)
            # A.Sleep(1)  # TODO: remove.

class Sub:
  def __init__(key1, re2, fn):
    .key1 = key1
    .re2 = regexp.MustCompile(re2) if re2 else None
    .fn = fn
    .str = repr(self)

  def __str__():
    return .str

class Thing:
  def __init__(origin, key1, key2, props):
    say 'CONSTRUCT THING', origin, key1, key2, props
    .origin = origin
    .key1 = key1
    .key2 = key2
    .props = props

pass  

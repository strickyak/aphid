from go import regexp, sync

Subs = {}
Mu = go_new(sync.Mutex)

def Subscribe(sub):
  Mu.Lock()
  with defer Mu.Unlock():
    if sub.key1 not in Subs:
      Subs[sub.key1] = {}
    Subs[sub.key1][str(sub)] = sub

def Unsubscribe(sub):
  Mu.Lock()
  with defer Mu.Unlock():
    del Subs[sub.key1][str(sub)]

def Publish(thing):
  Mu.Lock()
  with defer Mu.Unlock():
    d = Subs.get(thing.key1)
    if d:
      for sub in d.values():
        if not sub.re2 or sub.re2.FindString(thing.key2):
           go sub.fn(thing)

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

"""
skiplist.SkipList() is a sorted dictionary mapping strings to any value.
"""
from go import "github.com/huandu/skiplist" as base
from go import sync

class SkipList:
  def __init__():
    .sl = base.New(base.String)
    .mu = go_new(sync.Mutex)

  def Get(k):
    "Look up the value for string key k; return None if none."
    .mu.Lock()
    with defer .mu.Unlock():
      v, ok = .sl.GetValue(str(k))
      return v if ok else None

  def Put(k, v):
    "Set the value for string key k to v."
    .mu.Lock()
    with defer .mu.Unlock():
      .sl.Set(str(k), v)

  def Delete(k):
    "Delete item at string key k, returning the removed value, or None if not found."
    .mu.Lock()
    with defer .mu.Unlock():
      e = .sl.Remove(str(k))
      return e.Value if e else None

  def Items(k):
    "Return an iterator of (key, value) pairs, starting at string key k."
    # Locking this entire generator will lead to deadlock.
    # We could lock small bits, but it doesn't seem necessary.
    e = .sl.Get(str(k))
    while e:
      yield str(e.Key()), e.Value
      e = e.Next()

from go import github.com/syndtr/goleveldb/leveldb
from go/github.com/syndtr/goleveldb/leveldb import util

class Db:
  def __init__(path, recover=False):
    if recover:
      .db = leveldb.RecoverFile(path, None)
    else:
      .db = leveldb.OpenFile(path, None)

  def Close():
    .db.Close()

  def Get(key):
    return str(.db.Get(key, None))

  def Put(key, value):
    .db.Put(key, value, None)

  def Delete(key):
    .db.Delete(key, None)

  def Keys(prefix):
    iter = .db.NewIterator(util.BytesPrefix(prefix), None)
    with defer iter.Release():
      while iter.Next():
        yield str(iter.Key())
    iter.Error()

  def Items(prefix):
    iter = .db.NewIterator(util.BytesPrefix(prefix), None)
    with defer iter.Release():
      while iter.Next():
        yield str(iter.Key()), str(iter.Value())
    iter.Error()

  def Compact():
    .db.CompactRange(go_indirect(go_new(util.Range)))

pass

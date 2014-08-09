from . import rpc

class Client:
  def __init__(where):
    .where = where
    .r = rpc.Dial(where)

  def Get(path, pos, n):
    return .r.Call3("Get", path, pos, n)

  def List(path):
    return .r.Call1("List", path)

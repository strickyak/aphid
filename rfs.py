from . import rpc

class Client:
  def __init__(where):
    .where = where
    .r = rpc.Dial(where)

  def AReadAt(path, n, pos):
    return .r.Call3("AReadAt", path, n, pos)

  def AWriteAt(path, data, pos):
    return .r.Call3("AWriteAt", path, data, pos)

  def AListDir(path):
    return .r.Call1("AListDir", path)

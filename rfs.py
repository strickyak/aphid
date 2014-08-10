from . import rpc

class Client:
  def __init__(where):
    .where = where
    .r = rpc.Dial(where)

  def ReadAt(path, n, pos):
    return .r.Call3("ReadAt", path, n, pos)

  def WriteAt(path, data, pos):
    return .r.Call3("WriteAt", path, data, pos)

  def ListDir(path):
    return .r.Call1("ListDir", path)

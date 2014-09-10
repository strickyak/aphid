from go import os
from go import path/filepath

from go import github.com/strickyak/aphid

from . import rpc2
from . import flag

KEYNAME = byt('default')
KEY = byt('ABCDEFGHabcdefgh')

class RfsClient2(rpc2.Client2):
  def __init__(hostport, keyname, key):
    super(hostport, keyname, key)

  def AReadAt(path, n, pos):
    return .Call("AReadAt", [path, n, pos]).Wait()

  def AWriteAt(path, data, pos):
    return .Call("AWriteAt", [path, data, pos]).Wait()

  def AListDir(path):
    return .Call("AListDir", [path]).Wait()

def localPath(path):
  return filepath.Join(ROOT.X, path)

def AReadAt(path, n, pos):
  #say 'YYY <<< AReadAt', path, n, pos
  fd = os.Open(localPath(path))
  defer fd.Close()
  buf, eof = aphid.WrapReadAt(fd, n, pos)
  #say 'YYY >>> AReadAt', buf, eof
  return buf, eof

def AWriteAt(path, data, pos):
  fd = os.OpenFile(localPath(path), os.O_WRONLY | os.O_CREATE, 0666)
  defer fd.Close()
  return fd.WriteAt(data, pos)

def AListDir(path):
  fd = os.Open(localPath(path))
  defer fd.Close()
  vec = fd.Readdir(-1)
  z = [(i.Name(), i.IsDir(), i.Size(), i.ModTime().Unix()) for i in vec]
  return z

class RfsServer2(rpc2.Server2):
  def __init__(hostport, keyname, key):
    super(hostport, keyname, key)
    .Register('AListDir', AListDir)
    .Register('AReadAt', AReadAt)
    .Register('AWriteAt', AWriteAt)

PORT = flag.Int('port', 0, 'Port to listen on')
ROOT = flag.String('root', '', 'File system root')

def main(argv):
  argv = flag.Munch(argv)

  serv = RfsServer2('localhost:%d' % PORT.X, KEYNAME, KEY)
  serv.ListenAndServe()

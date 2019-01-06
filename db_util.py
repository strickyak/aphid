import db

def main(args):
  cmd = args[1]
  h = db.Db(args[0], recover=(cmd=='recover'))
  with defer h.Close():
    switch cmd:
      default:
        raise 'Unknown command: %q' % cmd
      case 'get':
        print h.Get(args[2])
      case 'put':
        h.Put(args[2], args[3])
      case 'delete':
        h.Delete(args[2])
      case 'keys':
        for k in h.Keys(args[2] if len(args)>2 else ''):
          print k
      case 'items':
        for k, v in h.Items(args[2] if len(args)>2 else ''):
          print k, '==', v
      case 'compact':
        h.Compact()
      case 'recover':
        pass

pass

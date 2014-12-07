from go import flag

port = flag.Int('port', 0, 'what port')

def main(argv):
  flag.Parse()
  say port
  say '%d' % int(port)

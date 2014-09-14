# Test 'fu' with 'find' command on /There/ rfs.
#
# This test depends on two things:
#   * Local tcp port 51234 is unused.
#   * /etc/init.d is present.

from . import rfs
from . import fu

def main(argv):
  rfs.PORT.X = 51234 
  rfs.ROOT.X = '/etc' 
  go rfs.main([])
  fu.main(['find', '/There/localhost:51234/init.d'])

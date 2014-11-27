from go import net/http

from . import A, bundle, flag
from . import aweber
from . import azoner

A_HTTP_BIND = flag.String('a_http_bind', ':8080', 'bind HTTP')

def main(args):
  args = flag.Munch(args)

  bundle.LoadBundles(topdir='.')

  # DNS Zones:
  zonedict = {}
  azoner.SlurpTriples(zonedict)
  go azoner.Serve(zonedict)

  # WEB:
  aweber.ProcessTriples()
  http.HandleFunc('/', aweber.RoutingFunc)
  http.ListenAndServe(A_HTTP_BIND.X , None)

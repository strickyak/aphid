from go import net/http

from . import A, bundle, flag
from . import aweber
from . import azoner
from . import keyring
from . import rbundle

FLAG_BUNDLE_TOPDIR = flag.String('a_bundle_topdir', '.', 'where are the bundles')
FLAG_RBUNDLE_BIND = flag.String('a_rbundle_bind', ':8081', 'bind remote bundle rpc')
FLAG_DNS_BIND = flag.String('a_dns_bind', ':8053', 'bind udp for dns')
FLAG_HTTP_BIND = flag.String('a_http_bind', ':8080', 'bind HTTP')
FLAG_RING = flag.String('a_keyring', 'test.ring', 'Test Keyring')

def main(args):
  args = flag.Munch(args)
  must not args, args

  # Load files.
  keyring.Load(FLAG_RING.X, keyring.Ring)

  # TODO -- triples for bundles, with config.
  #bundle.LoadBundles(topdir=FLAG_BUNDLE_TOPDIR.X)
  for k, v in flag.Triples.get('bundle', {}).items():
    bundle.LoadBundle(k, topdir=FLAG_BUNDLE_TOPDIR.X)

  for k, v in flag.Triples.get('xbundle', {}).items():
    key = keyring.Ring[v]
    must key
    must key.b_sym
    bundle.LoadBundle(k, topdir=FLAG_BUNDLE_TOPDIR.X, keyid=v, key=key.b_sym)

  for k, v in flag.Triples.get('wxbundle', {}).items():
    key = keyring.Ring[v]
    must key
    must key.b_sym
    # bundle.LoadBundle(k, topdir=FLAG_BUNDLE_TOPDIR.X, keyid=v, key=key.b_sym)
    # TODO: Cannot load the bundle now.   Loads on demand, then unloads.

  # Remote Bundle:
  go rbundle.RBundleServer(FLAG_RBUNDLE_BIND.X, keyring.Ring).ListenAndServe()

  # DNS Zones:
  zonedict = {}
  azoner.SlurpTriples(zonedict)
  go azoner.Serve(zonedict, FLAG_DNS_BIND.X)

  # WEB:
  aweber.ProcessTriples()
  http.HandleFunc('/favicon.ico', lambda w, r: None)
  http.HandleFunc('/', aweber.RoutingFunc)
  http.ListenAndServe(FLAG_HTTP_BIND.X , None)

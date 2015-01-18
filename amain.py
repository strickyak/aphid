from go import net/http
from go import path/filepath as F

from . import A, bundle, flag
from . import among
from . import aweber
from . import azoner
from . import keyring
from . import rbundle

FLAG_BUNDLE_TOPDIR = flag.String('a_bundle_topdir', '.', 'where are the bundles')
FLAG_RBUNDLE_BIND = flag.String('a_rbundle_bind', ':8081', 'bind remote bundle rpc')
FLAG_DNS_BIND = flag.String('a_dns_bind', ':8053', 'bind udp for dns')
FLAG_HTTP_BIND = flag.String('a_http_bind', ':8080', 'bind HTTP')
FLAG_RING = flag.String('a_keyring', 'test.ring', 'Test Keyring')
FLAG_ALL = flag.String('a_all', '', 'List of all connections to make')
FLAG_ME = flag.String('a_me', '', 'My id')

def main(args):
  args = flag.Munch(args)
  must not args, args

  # Load files.
  keyring.Load(FLAG_RING.X, keyring.Ring)

  for bname, v in flag.Triples.get('bundle', {}).items():
    bundir = F.Join(FLAG_BUNDLE_TOPDIR.X, 'b.%s' % bname)
    bundle.Bundles[bname] = bundle.Bundle(bname, bundir=bundir, suffix='0')

  for bname, v in flag.Triples.get('xbundle', {}).items():
    key = keyring.Ring[v]
    must key
    must key.b_sym
    bundir = F.Join(FLAG_BUNDLE_TOPDIR.X, 'b.%s' % bname)
    bundle.Bundles[bname] = bundle.Bundle(bname, bundir=bundir, suffix='0', keyid=v, key=key.b_sym)

  for bname, v in flag.Triples.get('wxbundle', {}).items():
    key = keyring.Ring[v]
    must key
    must key.b_sym
    must key.base
    bundle.Bundles[bname] = bundle.AttachedWebkeyBundle(
        bname, topdir=FLAG_BUNDLE_TOPDIR.X, suffix='0',
        webkeyid=v, webkey=key.b_sym, basekey=key.base)

  # Remote Bundle:
  go rbundle.RBundleServer(FLAG_RBUNDLE_BIND.X, keyring.Ring).ListenAndServe()

  # Synchronize changes among nodes.
  all_ids_map = A.ParseCommaEqualsDict(FLAG_ALL.X)
  am = among.Among(FLAG_ME.X, all_ids_map, keyring.Ring)
  am.Start()
  am.StartSyncronizer()

  # DNS Zones:
  zonedict = {}
  azoner.SlurpTriples(zonedict)
  go azoner.Serve(zonedict, FLAG_DNS_BIND.X)

  # WEB:
  aweber.ProcessTriples()
  http.HandleFunc('/favicon.ico', lambda w, r: None)
  http.HandleFunc('/', aweber.RoutingFunc)
  http.ListenAndServe(FLAG_HTTP_BIND.X , None)

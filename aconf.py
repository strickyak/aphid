from . import A, bundle, flag
from . import among
from . import aweber
from . import awiki
from . import azoner
from . import keyring
from . import rbundle

from go import net/http
from go import path/filepath as F
from go import github.com/strickyak/jsonnet_cgo as VM
from lib import data
import sys

def EvalFile(filename):
  vm = VM.Make()
  with defer vm.Destroy():
    return data.Eval(vm.EvaluateFile(filename))

class Conf:
  def __init__(filename):
    .filename = filename    
    .x = EvalFile(filename)
    .x_me = .x['me']
    .x_confname = .x['confname']
    .f_ip = .x['flags']['ip']
    .f_keyring = .x['flags']['keyring']
    .f_topdir = .x['flags']['topdir']
    .p_dns = .x['ports']['dns']
    .p_http = .x['ports']['http']
    .p_rpc = .x['ports']['rpc']
    .x_bundles = .x['bundles']
    .x_zones = .x['zones']
    .x_webs = .x['webs']
    .x_wikis = .x['wikis']

  def StartAll():
    .StartKeyring()
    .StartBundles()
    .StartZones()
    .StartWebHandlers()

  def StartKeyring():
    .ring = {}
    keyring.Load(.f_keyring, .ring)

  def StartBundles():
    .bundles = {}
    for bname, bx in .x_bundles.items():
      bundir = F.Join(.f_topdir, 'b.%s' % bname)
      switch bx['kind']:
        case 'plain':
          .bundles[bname] = bundle.Bundle(bname, bundir, suffix='0')
        case 'sym':
          keyid = bx['key']
          key = .ring[keyid]
          .bundles[bname] = bundle.Bundle(bname, bundir, suffix='0', keyid=keyid, key=key.b_sym)
        case 'websym':
          keyid = bx['key']
          key = .ring[keyid]
          .bundles[bname] = bundle.AttachedWebkeyBundle(
              bname, topdir=.f_topdir, suffix='0',
              webkeyid=keyid, webkey=key.b_sym, basekey=key.base)

    go rbundle.RBundleServer('%s:%d' % (.f_ip, .p_rpc), .ring).ListenAndServe()

  def StartZones():
    .zones = {}
    for zname, zx in .x_zones.items():
      bund = .bundles[zx['bundle']]
      body = bund.ReadFile(zx['zonefile'])
      must body
      azoner.ParseBody(.zones, body, zname)

    go azoner.Serve(.zones, '%s:%d' % (.f_ip, .p_dns))

  def StartWebHandlers():
    .handlers = {}
    for wname, wx in .x_webs.items():
      bname = wx['bundle']
      bund = .bundles[bname]
      .handlers[wname] = aweber.BundDir(bname, bund=bund).Handle4
    for wname, wx in .x_wikis.items():
      bname = wx['bundle']
      bund = .bundles[bname]
      .handlers[wname] = awiki.AWikiMaster(bname, bund=bund).Handler4
    aweber.HostHandlers = .handlers # TODO. grrr.

def main(args):
  args = flag.Munch(args)
  filename, = args

  conf = Conf(filename)
  conf.StartAll()

  http.HandleFunc('/favicon.ico', lambda w, r: None)
  http.HandleFunc('/', aweber.RoutingFunc)
  http.ListenAndServe('%s:%d' % (conf.f_ip, conf.p_http) , None)

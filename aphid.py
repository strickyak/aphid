from . import A, flag
from . import among, aweber, awiki, azoner
from . import bundle, keyring, pubsub, rbundle

from go import net/http, time
from go import path/filepath as F
from go import github.com/strickyak/jsonnet_cgo as VM
from lib import data
import sys

def EvalFile(filename):
  vm = VM.Make()
  with defer vm.Destroy():
    return data.Eval(vm.EvaluateFile(filename))

class Aphid:
  def __init__(filename, quit):
    .filename = filename    
    .quit = quit
    .x = EvalFile(filename)
    .x_me = .x['me']
    .x_confname = .x['confname']
    .f_ip = .x['flags']['ip']
    .f_keyring = .x['flags']['keyring']
    .f_topdir = .x['flags']['topdir']
    .p_dns = .x['ports']['dns']
    .p_http = .x['ports']['http']
    .p_https = .x['ports']['https']
    .p_rpc = .x['ports']['rpc']
    .x_bundles = .x['bundles']
    .x_zones = .x['zones']
    .x_webs = .x['webs']
    .x_wikis = .x['wikis']
    .x_peers = .x['peers']
    .bus = pubsub.Bus(self)

  def StartAll():
    .StartKeyring()
    .StartBundles()
    .StartZones()
    .StartWebHandlers()
    .StartAmong()

  def StartKeyring():
    .ring = {}
    keyring.Load(.f_keyring, .ring)

  def StartBundles():
    .bundles = {}
    for bname, bx in .x_bundles.items():
      bundir = F.Join(.f_topdir, 'b.%s' % bname)
      switch bx['kind']:
        case 'plain':
          .bundles[bname] = bundle.Bundle(self, bname, bundir, suffix='0')
        case 'sym':
          keyid = bx['key']
          key = .ring[keyid]
          .bundles[bname] = bundle.Bundle(self, bname, bundir, suffix='0', keyid=keyid, key=key.b_sym)
        case 'websym':
          keyid = bx['key']
          key = .ring[keyid]
          .bundles[bname] = bundle.AttachedWebkeyBundle(
              self, bname, topdir=.f_topdir, suffix='0',
              webkeyid=keyid, webkey=key.b_sym, basekey=key.base)

    go rbundle.RBundleServer(self, '%s:%d' % (.f_ip, .p_rpc), .ring).ListenAndServe()

  def StartZones():
    .zones = {}
    for zname, zx in .x_zones.items():
      bund = .bundles[zx['bundle']]
      body = bund.ReadFile(zx['zonefile'])
      must body
      azoner.ParseBody(.zones, body, zname, .f_ip)

    go azoner.Serve(.zones, '%s:%d' % (.f_ip, .p_dns))

  def StartWebHandlers():
    # Mux and Server.
    .mux = http.NewServeMux()
    # Add webs.
    for wname, wx in .x_webs.items():
      bname = wx['bundle']
      bund = .bundles[bname]
      obj = aweber.BundDir(self, bname, bund=bund)
      .mux.HandleFunc('%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s@/' % wname, obj.Handle2)
    # Add wikis.
    for wname, wx in .x_wikis.items():
      bname = wx['bundle']
      bund = .bundles[bname]
      obj = awiki.AWikiMaster(self, bname, bund=bund)
      .mux.HandleFunc('%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s@/' % wname, obj.Handle2)
    # Misc
    .mux.HandleFunc('/@@quit', lambda w, r: .quit.Put(1))
    # Go Serve.
    say 'SERVING', .server
    .server = go_new(http.Server) {
      Addr: '%s:%d' % (.f_ip, .p_http),
      Handler: .mux,
      ReadTimeout:    10 * time.Second,
      WriteTimeout:   10 * time.Second,
    }
    go .server.ListenAndServe()
    if .p_https:
      .tlsserver = go_new(http.Server) {
        Addr: '%s:%d' % (.f_ip, .p_https),
        Handler: .mux,
        ReadTimeout:    10 * time.Second,
        WriteTimeout:   10 * time.Second,
      }
      go .tlsserver.ListenAndServeTLS("cacert.pem", "privkey.pem")

  def StartAmong():
    peer_map = dict([(k, '%s:%d' % (v['host'], v['port'])) for k, v in .x_peers.items()])
    say peer_map
    am = among.Among(self, .x_me, peer_map)
    am.Start()
    am.StartSyncronizer()

def main(args):
  args = flag.Munch(args)
  quit = rye_chan(1)

  for filename in args:
    a = Aphid(filename, quit)
    say 'STARTING', filename
    a.StartAll()
    A.Sleep(0.1)

  say 'WAITING'
  quit.Take()
  say 'QUITTING'

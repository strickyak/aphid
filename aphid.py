from . import A, flag
from . import among, aweber, awiki, awedit, azoner, formic
from . import bundle, keyring, pubsub, rbundle

from go import fmt, net/http, time
from go import path/filepath as F
from go import github.com/strickyak/jsonnet_cgo as VM
from lib import data
import sys

VmImports = {}
def EvalFileOrSnippet(filename, snippet=None, imports=None):
  vm = VM.Make()
  with defer vm.Destroy():
    if snippet:
      VmImports[filename] = snippet
      vm.ImportCallback(lambda rel, name: VmImports.get(name, 'ERROR UKNOWN_IMPORT: %q' % name))
      say filename
      say snippet
      js = vm.EvaluateSnippet(filename, snippet)
      say js
      return data.Eval(js)
    else:
      js = vm.EvaluateFile(filename)
      say js
      return data.Eval(js)

class Aphid:
  def __init__(quit, filename, snippet=None, imports=None):
    .quit = quit
    .filename = filename
    .snippet = snippet
    .x = EvalFileOrSnippet(filename=filename, snippet=snippet, imports=imports)
    .x_me = .x['me']
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
    .x_formic = .x['formic']
    .x_peers = .x['peers']
    .bus = pubsub.Bus(self)

  def __str__():
    return 'Aphid{%q}' % .filename
  def __repr__():
    return .__str__()

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
          .bundles[bname] = bundle.PlainBundle(self, bname=bname, bundir=bundir, suffix='0')
        case 'sym':
          keyid = bx['key']
          key = .ring[keyid]
          .bundles[bname] = bundle.RedhedBundle(self, bname=bname, bundir=bundir, suffix='0', keyid=keyid, key=key.b_sym)
        case 'websym':
          keyid = bx['key']
          key = .ring[keyid]
          .bundles[bname] = bundle.WebkeyBundle(
              self, bname, topdir=.f_topdir, suffix='0',
              webkeyid=keyid, webkey=key.b_sym, basekey=key.base)

    go rbundle.RBundleServer(self, '%s:%d' % (.f_ip, .p_rpc), .ring).ListenAndServe()

  def StartZones():
    .zones = {}
    for zname, zx in .x_zones.items():
      bund = .bundles[zx['bundle']]
      body = bundle.ReadFile(bund, zx['zonefile'])
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
      .mux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .mux.HandleFunc('/@%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s@e' % wname, awedit.Master(self, bname, bund=bund).Handle2)
    # Add wikis.
    for wname, wx in .x_wikis.items():
      bname = wx['bundle']
      bund = .bundles[bname]
      obj = awiki.AWikiMaster(self, bname, bund=bund)
      .mux.HandleFunc('%s/' % wname, obj.Handle2)
      .mux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .mux.HandleFunc('/@%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s@e' % wname, awedit.Master(self, bname, bund=bund).Handle2)
    # Add formic.
    for wname, config in .x_formic.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = formic.FormicMaster(self, bname, bund=bund, config=config)
      .mux.HandleFunc('%s/' % wname, obj.Handle2)
      .mux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .mux.HandleFunc('/@%s/' % wname, obj.Handle2)
      .mux.HandleFunc('/@%s@e/' % wname, awedit.Master(self, bname, bund=bund).Handle2)
      say ('%s/' % wname)
      say ('%s:%d/' % (wname,  .p_http))
      say ('/@%s/' % wname)
      say ('/@%s@e/' % wname)
      say 'WEDIT', '/@%s@e/' % wname
    # Misc
    .mux.HandleFunc('/@@quit', lambda w, r: .quit.Put(1))

    def Otherwise(w, r):
      w.WriteHeader(http.StatusNotFound)
      fmt.Fprintf(w, "404 NOT FOUND\n\n")
      fmt.Fprintf(w, "[aphid] Proto: %q Method: %q\n", r.Proto, r.Method)
      fmt.Fprintf(w, "[aphid] Host: %q Path: %q\n", r.Host, r.URL.Path)
      fmt.Fprintf(w, "[aphid] Header:\n")
      for k, v in sorted(r.Header.items()):
        for e in v:
          fmt.Fprintf(w, "[aphid]   %q : %q\n", k, e)
    .mux.HandleFunc('/', Otherwise)

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

def LaunchConfigFiles(quit, filenames):
  for filename in filenames:
    say 'LAUNCHING', filename
    a = Aphid(quit, filename)
    say 'STARTING', filename
    a.StartAll()
    A.Sleep(0.1)

def main(args):
  args = flag.Munch(args)
  quit = rye_chan(1)
  LaunchConfigFiles(quit=quit, filenames=args)

  say 'WAITING'
  quit.Take()
  say 'QUITTING'

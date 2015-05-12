from . import A, flag
from . import among, aweber, awiki, awedit, azoner, formic
from . import bundle, keyring, pubsub, rbundle

from go import bufio, fmt, net/http, os, time
from go import path as P, path/filepath as F
from go import github.com/strickyak/jsonnet_cgo as VM
from lib import data
import sys

SEEDDIR = flag.String('seeddir', '', 'Directory containing bundle seed files')

def PJ(*vec):
  return P.Clean(P.Join(*vec))
def FJ(*vec):
  return F.Clean(F.Join(*vec))

def EvalConfig(filename):
  vm = VM.Make()
  with defer vm.Destroy():
    # Convert to JSON string.
    js = vm.EvaluateFile(filename)
    say js
    # Eval the JSON into a Python value.
    return data.Eval(js)

class Aphid:
  def __init__(quit, filename):
    .quit = quit
    .filename = filename

    .x = EvalConfig(filename)
    .x_me = .x['me']
    .f_ip = .x['flags']['ip']
    .f_keyring = .x['flags']['keyring']
    .f_topdir = .x['flags']['topdir']
    .f_domain = .x['flags'].get('domain', '')
    .p_dns = .x['ports']['dns']
    .p_http = .x['ports']['http']
    .p_https = .x['ports']['https']
    .p_rpc = .x['ports']['rpc']
    .x_bundles = .x['bundles']
    .x_zones = .x['zones']
    .x_webs = .x['webs']
    .x_wikis = .x['wikis']
    .x_formics = .x['formics']
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
      if SEEDDIR.X:
        .LoadBundleSeedFiles(bname, .bundles[bname], SEEDDIR.X)

    go rbundle.RBundleServer(self, '%s:%d' % (.f_ip, .p_rpc), .ring).ListenAndServe()

  def LoadBundleSeedFiles(bname, bund, seeddir):
    t = FJ(seeddir, bname)
    def fn(path, info, err):
      say path, info, err
      if not info or info.IsDir():
        return None  # No error.

      assert path[:len(t)] == t
      assert path[len(t)] == '/'
      fpath = path[len(t)+1:]  # Remove prefix and one '/'
  
      fd = os.Open(path)
      with defer fd.Close():
        br = bufio.NewReader(fd)
        cr = bundle.ChunkReaderAdapter(br)
        cw = bund.MakeWriter(fpath, pw=None, mtime=0, raw=None)
        bundle.CopyChunks(cw, cr)
        cw.Close()
      return None  # No error.
    F.Walk(t, fn)

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
    for wname, config in .x_webs.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = aweber.BundDir(self, bname, bund=bund)
      if config.get('domainly'):
        .mux.HandleFunc('%s/' % wname, obj.Handle2)
        .mux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .mux.HandleFunc('%s/@%s/' % (.f_domain, wname), obj.Handle2)
      .mux.HandleFunc('%s/@%s@e' % (.f_domain, wname), awedit.Master(self, bname, bund=bund).Handle2)
    # Add wikis.
    for wname, config in .x_wikis.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = awiki.AWikiMaster(self, bname, bund=bund)
      if config.get('domainly'):
        .mux.HandleFunc('%s/' % wname, obj.Handle2)
        .mux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .mux.HandleFunc('%s/@%s/' % (.f_domain, wname), obj.Handle2)
      .mux.HandleFunc('%s/@%s@e' % (.f_domain, wname), awedit.Master(self, bname, bund=bund).Handle2)

    # Add formic.
    for wname, config in .x_formics.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = formic.FormicMaster(self, bname, bund=bund, config=config)
      .mux.HandleFunc(wname, obj.Handle2)
      say 'formic .mux.HandleFunc %q' % wname
      for a in config.get('aliases'):
        .mux.HandleFunc(a, obj.Handle2)
        say 'formic .mux.HandleFunc %q' % a

    ## Misc
    #.mux.HandleFunc('/@@quit', lambda w, r: .quit.Put(1))

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
  quit.Recv()
  say 'QUITTING'

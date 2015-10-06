from . import A, flag
from . import among, aweber, awiki, awedit, azoner, formic, smilax4, stash
from . import bundle, keyring, pubsub, rbundle
from . import laph

from go import bufio, fmt, html, io/ioutil, net/http, os, time
from go import path as P, path/filepath as F
from go import github.com/strickyak/jsonnet_cgo as VM

from lib import data
import sys

SEEDDIR = flag.String('seeddir', '', 'Directory containing bundle seed files')

Esc = html.EscapeString

def PJ(*vec):
  return P.Clean(P.Join(*vec))
def FJ(*vec):
  return F.Clean(F.Join(*vec))

SnippetMemory = {}
def EvalConfig(filename, snippet=None):
  vm = VM.Make()

  def importSnippet(base, rel):
    importName = P.Clean(P.Join(base, rel))
    if importName in SnippetMemory:
      say base, rel, importName, SnippetMemory[importName]
      #say SnippetMemory[importName][1700:]
      #say SnippetMemory[importName][1790:]
      return SnippetMemory[importName]
    else:
      say '????????????????????', False
      return '????????????????????'
  vm.ImportCallback(importSnippet)

  with defer vm.Destroy():
    # Convert to JSON string.
    if snippet:
      say filename, snippet
      js = vm.EvaluateSnippet(filename, snippet)
      SnippetMemory[filename] = snippet  # For future use.
    else:
      js = vm.EvaluateFile(filename)
    say js
    #print >>os.Stderr, js
    #say js[1700:]
    #say js[1730:]
    # Eval the JSON into a Python value.
    return data.Eval(js)

class Mux:
  def __init__():
    .mux = http.NewServeMux()
    .mux.HandleFunc('/', .Otherwise)
    .paths = {}

  def HandleFunc(path, func):
    .mux.HandleFunc(path, func)
    .paths[path] = func

  def Otherwise(w, r):
    w.Header().Set('Content-Type', 'text/html; charset=UTF-8')
    w.WriteHeader(http.StatusNotFound)
    try:
      fmt.Fprintf(w, Esc("404 NOT FOUND (Path prefix not registered)\n\n") + '<br><p>')
      fmt.Fprintf(w, Esc("[aphid] Proto: %q Method: %q\n" % ( r.Proto, r.Method)) + '<br><p>')
      fmt.Fprintf(w, Esc("[aphid] Host: %q Path: %q\n" % (r.Host, r.URL.Path)) + '<br><p>')
      for k, v in sorted(r.Header.items()):
        for e in v:
          fmt.Fprintf(w, Esc("[aphid] Header: %q : %q\n" % (k, e)) + '<br>')
      fmt.Fprintf(w, '<br><p>')

      fmt.Fprintf(w, 'Are you looking for one of these?<ul>')
      for k in sorted(.paths.keys()):
        if k.startswith('/'):
          fmt.Fprintf(w, '<li> <a href="%s">%s</a>', k, Esc(k))
        else:
          fmt.Fprintf(w, '<li> <a href="http://%s">%s</a>', k, Esc(k))
      fmt.Fprintf(w, '</ul>')
    except as ex:
      fmt.Fprintf(w, '<br><br><tt>******* EXCEPTION ******* %s' % Esc(str(ex)))

class Aphid:
  def __init__(quit, filename, snippet=None):
    .quit = quit
    .filename = filename

    laphfile, part = filename.split(':', 1)
    laphexpr = ioutil.ReadFile(laphfile)
    .laph = laph.Compile(laphexpr)
    js = .laph.ToJson(part)
    .x = data.Eval(js)

    say .x
    .x_me = .x['me']
    .f_ip = .x['flags']['ip']
    .f_topdir = .x['flags']['topdir']
    .f_domain = .x['flags'].get('domain', '')
    say .x['ports']
    .p_dns = int(.x['ports'].get('dns', 0))
    .p_http = int(.x['ports']['http'])
    .p_https = int(.x['ports']['https'])
    .p_rpc = int(.x['ports']['rpc'])
    .x_bundles = .x['bundles']
    .x_zones = .x.get('zones', {})
    .x_webs = .x.get('webs', {})
    .x_wikis = .x.get('wikis', {})
    .x_formics = .x.get('formics', {})
    .x_smilax4 = .x.get('smilax4', {})
    .x_stash = .x.get('stash', {})
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
    keyring.Load()
    .ring = keyring.Ring

  def StartBundles():
    .bundles = {}
    for bname, bx in .x_bundles.items():
      bundir = F.Join(.f_topdir, 'b.%s' % bname)
      switch bx['kind']:
        case 'plain':
          .bundles[bname] = bundle.PlainBundle(self, bname=bname, bundir=bundir, suffix='0')
        case 'sym':
          keyid = bx['key']
          key = keyring.Ring[keyid]
          say keyid, key.b_sym, key, bx
          .bundles[bname] = bundle.RedhedBundle(self, bname=bname, bundir=bundir, suffix='0', keyid=keyid, key=key.b_sym)
        case 'websym':
          keyid = bx['key']
          key = keyring.Ring[keyid]
          say keyid, bx, key
          .bundles[bname] = bundle.WebkeyBundle(
              self, bname, topdir=.f_topdir, suffix='0',
              webkeyid=keyid, xorkey=key.b_xor, basekey=key.base)
      if SEEDDIR.X:
        .LoadBundleSeedFiles(bname, .bundles[bname], SEEDDIR.X)

    go rbundle.RBundleServer(self, '%s:%d' % (.f_ip, .p_rpc), keyring.Ring).ListenAndServe()

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
    say '@@@ walking', t, fn
    F.Walk(t, fn)

  def StartZones():
    if .p_dns:
      .zones = {}
      for zname, zx in .x_zones.items():
        if zname == '*':
          bund = .bundles[zx['bundle']]
          zonedir = zx['zonedir']
          for g in bund.ListFiles(zonedir):
            body = bundle.ReadFile(bund, P.Join(zonedir, g))
            must body
            azoner.ParseBody(.zones, body, P.Base(g), .f_ip)
        else:
          bund = .bundles[zx['bundle']]
          body = bundle.ReadFile(bund, zx['zonefile'])
          must body
          azoner.ParseBody(.zones, body, zname, .f_ip)

      go azoner.Serve(.zones, '%s:%d' % (.f_ip, .p_dns))

  def StartWebHandlers():
    # Mux and Server.
    #// .mux = http.NewServeMux()
    .mux = Mux()

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
      for k in config.get('paths'):
        v = config['paths'][k]
        .mux.HandleFunc(v, obj.Handle2)
        say 'formic .mux.HandleFunc %q' % k

    # Add smilax4.
    for wname, config in .x_smilax4.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = smilax4.Smilax4Master(self, bname, bund=bund, config=config)
      .mux.HandleFunc(wname, obj.Handle2)
      say 'smilax4 .mux.HandleFunc %q' % wname
      for k in config.get('paths'):
        v = config['paths'][k]
        .mux.HandleFunc(v, obj.Handle2)
        say 'smilax4 .mux.HandleFunc %q' % k

    # Add stash.
    for wname, config in .x_stash.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = stash.StashMaster(self, bname, bund=bund, config=config)
      .mux.HandleFunc(wname, obj.Handle2)
      say 'stash name %q' % wname
      for k in config.get('paths'):
        v = config['paths'][k]
        .mux.HandleFunc(v, obj.Handle2)
        say 'stash alias %q' % k

    ## Misc
    #.mux.HandleFunc('/@@quit', lambda w, r: .quit.Put(1))

    # Go Serve.
    say 'SERVING', .server
    .server = go_new(http.Server) {
      Addr: '%s:%d' % (.f_ip, .p_http),
      Handler: .mux.mux,
      ReadTimeout:    10 * time.Second,
      WriteTimeout:   10 * time.Second,
    }
    go .server.ListenAndServe()
    if .p_https:
      .tlsserver = go_new(http.Server) {
        Addr: '%s:%d' % (.f_ip, .p_https),
        Handler: .mux.mux,
        ReadTimeout:    10 * time.Second,
        WriteTimeout:   10 * time.Second,
      }
      go .tlsserver.ListenAndServeTLS("cacert.pem", "privkey.pem")

  def StartAmong():
    peer_map = dict([(v['num'], '%s:%d' % (v['host'], int(v['port']))) for _, v in .x_peers.items()])
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

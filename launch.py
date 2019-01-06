import A, flag
import among, amux, aweber, awiki, awedit, azoner, formic, smilax4, stash
import bundle, keyring, laph3, pubsub, rbundle, util
from go import bufio, fmt, html, io.ioutil, net.http, os, regexp, time
from go import path as P, path.filepath as F
from "github.com/strickyak/rye/contrib" import data

SEEDDIR = flag.String('seeddir', '', 'Directory containing bundle seed files')

def FJ(*vec):
  return F.Clean(F.Join(*vec))

class Aphid:
  def __init__(quit, filename, snippet=None):
    .quit = quit
    .filename = filename

    laphfile, part = filename.split(':', 1)
    laphexpr = ioutil.ReadFile(laphfile)

    .laph = laph3.Compile(laphexpr)
    .x = .laph.EvalPath(part)
    #say .x
    util.PrettyPrint(.x)

    .x_me = .x['me']
    .f_ip = .x['flags']['ip']
    .f_topdir = .x['flags']['topdir']
    .f_domain = .x['flags'].get('domain', '')
    #say .x['ports']
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
        case 'posix':
          .bundles[bname] = bundle.PosixBundle(self, bname=bname, bundir=bundir, suffix='0')
        case 'plain':
          .bundles[bname] = bundle.PlainBundle(self, bname=bname, bundir=bundir, suffix='0')
        case 'sym':
          keyid = bx['key']
          key = keyring.Ring[keyid]
          #say keyid, key.b_sym, key, bx
          .bundles[bname] = bundle.RedhedBundle(self, bname=bname, bundir=bundir, suffix='0', keyid=keyid, key=key.b_sym)
        case 'websym':
          keyid = bx['key']
          key = keyring.Ring[keyid]
          #say keyid, bx, key
          .bundles[bname] = bundle.WebkeyBundle(
              self, bname, topdir=.f_topdir, suffix='0',
              webkeyid=keyid, xorkey=key.b_xor, basekey=key.base)
      if SEEDDIR.X:
        #say SEEDDIR.X, bname, '.LoadBundleSeedFiles ('
        .LoadBundleSeedFiles(bname, .bundles[bname], SEEDDIR.X)
        #say SEEDDIR.X, bname, '.LoadBundleSeedFiles )'

    go rbundle.RBundleServer(self, '%s:%d' % (.f_ip, .p_rpc), keyring.Ring).ListenAndServe()

  def LoadBundleSeedFiles(bname, bund, seeddir):
    #say bname, type(bund), seeddir
    t = FJ(seeddir, bname)
    def fn(path, info, err):
      #say path, info, err
      if not info or info.IsDir():
        return None  # No error.

      assert path[:len(t)] == t
      assert path[len(t)] == '/'
      fpath = path[len(t)+1:]  # Remove prefix and one '/'

      #say bname, path, 'COPY ('
      body = str(ioutil.ReadFile(path))
      bundle.WriteFile(bund, fpath, body, pw=None, mtime=0, raw=False)
      #say bname, path, 'COPY )'
  
      #fd = os.Open(path)
      #with defer fd.Close():
      #  br = bufio.NewReader(fd)
      #  cr = bundle.ChunkReaderAdapter(br)
      #  cw = bund.MakeWriter(fpath, pw=None, mtime=0, raw=None)
      #  bundle.CopyChunks(cw, cr)
      #  cw.Close()

      return None  # No error.
    #say '@@@ walking', t, fn
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
    # AMux and Server.
    .amux = amux.AMux()

    # Add webs.
    for wname, config in .x_webs.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = aweber.BundDir(self, bname, bund=bund)
      if config.get('domainly'):
        .amux.HandleFunc('%s/' % wname, obj.Handle2)
        .amux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .amux.HandleFunc('%s/@%s/' % (.f_domain, wname), obj.Handle2)
      .amux.HandleFunc('%s/@%s*/' % (.f_domain, wname), awedit.Master(self, bname, bund=bund).Handle2)
    # Add wikis.
    for wname, config in .x_wikis.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = awiki.AWikiMaster(self, bname, bund=bund)
      if config.get('domainly'):
        .amux.HandleFunc('%s/' % wname, obj.Handle2)
        .amux.HandleFunc('%s:%d/' % (wname, .p_http), obj.Handle2)
      .amux.HandleFunc('%s/@%s/' % (.f_domain, wname), obj.Handle2)
      .amux.HandleFunc('%s/@%s*/' % (.f_domain, wname), awedit.Master(self, bname, bund=bund).Handle2)

    # Add formic.
    #say .filename, .x_formics.items()
    for wname, config in .x_formics.items():
      #say wname, config
      bname = config['bundle']
      bund = .bundles[bname]
      obj = formic.FormicMaster(self, bname, bund=bund, config=config)
      .amux.HandleFunc(wname, obj.Handle2)
      say 'formic .amux.HandleFunc %q' % wname
      for k in config.get('paths'):
        v = config['paths'][k]
        .amux.HandleFunc(v, obj.Handle2)
        say 'formic .amux.HandleFunc %q' % k

    say 'Skipping smilax until later'
    # Add smilax4.
    #for wname, config in .x_smilax4.items():
    #  bname = config['bundle']
    #  bund = .bundles[bname]
    #  obj = smilax4.Smilax4Master(self, bname, bund=bund, config=config)
    #  .amux.HandleFunc(wname, obj.Handle2)
    #  say 'smilax4 .amux.HandleFunc %q' % wname
    #  for k in config.get('paths'):
    #    v = config['paths'][k]
    #    .amux.HandleFunc(v, obj.Handle2)
    #    say 'smilax4 .amux.HandleFunc %q' % k

    # Add stash.
    for wname, config in .x_stash.items():
      bname = config['bundle']
      bund = .bundles[bname]
      obj = stash.StashMaster(self, bname, bund=bund, config=config)
      .amux.HandleFunc(wname, obj.Handle2)
      say 'stash name %q' % wname
      for k in config.get('paths'):
        v = config['paths'][k]
        .amux.HandleFunc(v, obj.Handle2)
        say 'stash alias %q' % k

    # Go Serve.
    say 'SERVING', .server
    .server = setattrs(go_new(http.Server),
      Addr= '%s:%d' % (.f_ip, .p_http),
      Handler= .amux.mux,
      ReadTimeout=    10 * time.Second,
      WriteTimeout=   10 * time.Second,
    )
    go .server.ListenAndServe()
    if .p_https:
      .tlsserver = setattrs(go_new(http.Server),
        Addr= '%s:%d' % (.f_ip, .p_https),
        Handler= .amux.mux,
        ReadTimeout=    10 * time.Second,
        WriteTimeout=   10 * time.Second,
      )
      go .tlsserver.ListenAndServeTLS("cacert.pem", "privkey.pem")

  def StartAmong():
    peer_map = dict([(k, '%s:%d' % (v['host'], int(v['port']))) for k, v in .x_peers.items()])
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

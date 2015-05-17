from go import bytes, os, io, io/ioutil
from go import mime/multipart, net/http
from go import encoding/base64
from go import path/filepath as FP
from . import A, aphid, au, bundle, sym, util

Ring = None

TERMITE1 = '''{
  me: 11,

  confname: "termite" + $.me,

  flags: {
    ip:        "127.0.0.1",
    topdir:    "__termite__" + $.confname,
    keyring:   "test.ring",
  },

  peers: {
    "11": { host: "127.0.0.1", port: 28181, name: "termite11" },
    "12": { host: "127.0.0.1", port: 28281, name: "termite12" },
    "13": { host: "127.0.0.1", port: 28381, name: "termite13" },
  },

  ports: {
    base::  $.peers[""+$.me].port - self.rpcoff,

    dnsoff::   53,
    httpoff::  80,
    httpsoff::  43,
    rpcoff::   81,

    dns:   self.base + self.dnsoff,
    http:  self.base + self.httpoff,
    https: self.base + self.httpsoff,
    rpc:   self.base + self.rpcoff,
  },

  bundles: {
    "termite0": { kind: "plain" },
    "termite1": { kind: "plain" },
    "termite2": { kind: "sym", key: "YAK" },
    "termite3": { kind: "websym", key: "WLM" },
    "termite3peek": { kind: "websym", key: "BLM" },
  },

  zones: {
    "aphid.cc": {
      "bundle": "termite0",
      "zonefile": "dns/aphid.cc",
    },
  },

  webs: {
    "termite0": { bundle: "termite0" },
    "termite1": { bundle: "termite1" },
    "termite2": { bundle: "termite2" },
    "termite3": { bundle: "termite3" },
  },

  wikis: {
    "wiki": { bundle: "termite0" },
    "web": { bundle: "termite0" },
    "wiki.termite0.aphid.cc": { bundle: "termite0" },
    "termite1.wiki": { bundle: "termite1" },
    "termite2.wiki": { bundle: "termite2" },
    "termite3.wiki": { bundle: "termite3" },
  },

  formics: {
    local trivial_pw = "f5606220aa1e4ab012a6cc32cc980dd9", // "password"
    "/@termite1.formic/": { bundle: "termite1", md5pw: trivial_pw },
    "/@termite2.formic/": { bundle: "termite2", md5pw: trivial_pw },
  },
}'''
TERMITE2 = '''import "termite1.conf" {
  me: 12,

  flags: super.flags {
    verbose: 5,
  },

  ports: super.ports {
    debug: self.base + 99,
  },

  webs: super.webs {
    "extra.termite0.aphid.cc": { bundle: "termite0" },
  },

  wikis: super.wikis {
    "extra.wiki.termite0.aphid.cc": { bundle: "termite0" },
  },

  formics: super.formics {},
}'''
TERMITE3 = '''import "termite1.conf" {
  me: 13,
  zones: {},
  webs: {},
  wikis: {},
  formics: {},
}'''

def Clear():
  for d in ['__termite_local', '__termite__termite11', '__termite__termite12', '__termite__termite13']:
    os.RemoveAll(d)
    os.Mkdir(d, 0777)
    if not d.endswith('local'):
      for b in ['b.termite0', 'b.termite1', 'b.termite2', 'b.termite3']:
        os.Mkdir(FP.Join(d, b), 0777)
    os.Symlink('b.termite3', FP.Join(d, 'b.termite3peek')) 

  os.MkdirAll('__termite_local/termite0/dns', 0777)
  ioutil.WriteFile(
      '__termite_local/termite0/dns/aphid.cc',
      'aphid.cc. IN NS cubic.yak.net.\n',
      0666)

def CopyFilesDirToDir(dest, src):
  say dest, src
  os.MkdirAll(dest, 0777)
  for f in FP.Glob(FP.Join(src, '*')):
    say f, dest
    b = FP.Base(f)
    r = os.Open(FP.Join(src, b))
    w = os.Create(FP.Join(dest, b))
    io.Copy(w, r)
    w.Close()
    r.Close()

def Cmp(file1, file2):
  say file1
  say file2
  x1 = ioutil.ReadFile(file1)
  x2 = ioutil.ReadFile(file2)
  say len(x1), len(x2)
  must x1 == x2

def Glob1(*names):
  say names
  vec = FP.Glob(FP.Join('.', *names))
  say names, vec
  must len(vec) == 1
  return vec[0]

def LoadTermite(i):
  say i
  for cmd in ['BigLocalDir', 'BigRemoteDir', 'SPush', 'BigLocalDir', 'BigRemoteDir']:
    say '@@@@@@@@@@@@@@@@@@@@@@@@@ Building:', i, cmd
    # bund = 'termite%d' % i if i<3 else 'termite%dpeek' % i
    bund = 'termite%d' % i
    pw = 'password' if i>2 else ''
    fullcmd = [
        '--bund=%s' % bund, '--dir=./__termite_local', '--server=127.0.0.1:28381',
        '--cid=91', '--sid=92', '--exit=0', '--pw=%s' % pw,
        cmd]
    say '@@@@@@@@@@@@@@@@@@@@@@@@@ Running:', i, fullcmd
    au.main(fullcmd)
    say '@@@@@@@@@@@@@@@@@@@@@@@@@ Ran:', i
    if cmd == 'SPush':
      A.Sleep(1)

def HttpUpload(url, basename, params, r, pw=None):
  # Thanks: http://matt.aimonetti.net/posts/2013/07/01/golang-multipart-file-upload-example/
  body = go_new(bytes.Buffer)
  writer = multipart.NewWriter(body)
  part = writer.CreateFormFile('file', basename)
  io.Copy(part, r)
  for k, v in params.items():
    writer.WriteField(k, v)
  writer.Close()
  say body.String()
  req = http.NewRequest("POST", url, body)
  say req
  return HttpFinishReq(req, ct=writer.FormDataContentType(), pw=pw)

def HttpMethod(method, url, body='', pw=None):
  client = go_new(http.Client)
  bb = bytes.NewBuffer(body)
  req = http.NewRequest(method, url, bb)
  return HttpFinishReq(req, 'application/x-www-form-urlencoded' if method == 'POST' else None, pw=pw)

def HttpFinishReq(req, ct, pw):
  client = go_new(http.Client)
  if pw:
    encoded = base64.StdEncoding.EncodeToString('user:%s' % pw)
    req.Header.Add('Authorization', 'Basic %s' % encoded)
  if ct:
    req.Header.Add('Content-Type', ct)
  say req.Header
  resp = client.Do(req)
  z99 = ioutil.ReadAll(resp.Body)
  resp.Body.Close()
  say z99, resp
  return z99

def main(_):
  Clear()
  quit = rye_chan(1)
  t1 = aphid.Aphid(quit=quit, filename='termite1.conf', snippet=TERMITE1)
  t2 = aphid.Aphid(quit=quit, filename='termite2.conf', snippet=TERMITE2)
  t3 = aphid.Aphid(quit=quit, filename='termite3.conf', snippet=TERMITE3)

  t3.StartAll()
  global Ring
  Ring = t3.ring

  bt2 = t3.bundles['termite2']
  say bt2, bt2.bundir
  bundle.WriteFile(bt2, 'abcde/lmnop/wxyz.txt', 'oscar meyer wiener')
  say 'Wrote it'
  x = bundle.ReadFile(bt2, 'abcde/lmnop/wxyz.txt')
  say 'Red it', x

  A.Sleep(1)
  LoadTermite(0)

  CopyFilesDirToDir(
      '__termite__termite11/b.termite0/d.dns/f.aphid.cc/',
      '__termite__termite13/b.termite0/d.dns/f.aphid.cc/')
  CopyFilesDirToDir(
      '__termite__termite12/b.termite0/d.dns/f.aphid.cc/',
      '__termite__termite13/b.termite0/d.dns/f.aphid.cc/')

  t1.StartAll()
  A.Sleep(1)
  t2.StartAll()
  A.Sleep(4)

  HELLO_APHID = 'Hello Aphid!\n'
  for i in range(4):
    say i
    os.MkdirAll('__termite_local/termite%d/web/frog' % i, 0777)
    ioutil.WriteFile(
        '__termite_local/termite%d/web/frog/index.html' % i,
        HELLO_APHID,
        0666)
    say i
    LoadTermite(i)
    A.Sleep(1)
    say i

    x = ioutil.ReadFile('__termite_local/termite0/web/frog/index.html')
    print x
    must len(x) == 13
    must x == byt(HELLO_APHID)

    pw = 'password' if i>2 else None
    for t in [t3, t2, t1]:
      say i, str(t)
      y = bundle.ReadFile(t.bundles['termite%d' % i], 'web/frog/index.html', pw=pw)
      print x, y
      must byt(x)==byt(y), (i, str(t), x, y)

    #Cmp(Glob1('__termite__termite13/b.termite%d/d.web/d.frog/f.index.html/r.*.13.*' % i),
    #    Glob1('__termite_local/termite0/web/frog/index.html'))
    #Cmp(Glob1('__termite__termite13/b.termite%d/d.web/d.frog/f.index.html/r.*.13.*' % i),
    #    Glob1('__termite__termite11/b.termite%d/d.web/d.frog/f.index.html/r.*.13.*' % i))
    #Cmp(Glob1('__termite__termite13/b.termite%d/d.web/d.frog/f.index.html/r.*.13.*' % i),
    #    Glob1('__termite__termite12/b.termite%d/d.web/d.frog/f.index.html/r.*.13.*' % i))

  # Install a template for /formic/layouts/_default/single.html
  buf = bytes.NewBuffer('Default Single Template\n')
  z0 = HttpUpload(
      url='http://localhost:28180/@termite1.formic/*attach_media_submit?',
      basename='single.html',
      params=dict(foo='bar', EditDir='/formic/layouts/_default'),
      r=buf,
      pw='password')
  say z0

  # Submit a home page.
  body = util.ConstructQueryFromDict(dict(
        submit='Save',
        EditPath='home',
        EditMd='HelloHomePage%0A',
        EditTitle='HomePage',
        EditMainName='',
        EditMainWeight='0',
        EditType='',
        EditAliases=''))
  z1 = HttpMethod('POST', 'http://localhost:28180/@termite1.formic/*edit_page_submit?', body=body, pw='password')
  say z1

  # Get the home page.
  A.Sleep(1)
  z2 = HttpMethod('GET', 'http://localhost:28180/@termite1.formic/home?', body='', pw='password')
  say z2

  say "OKAY termite_test.py"

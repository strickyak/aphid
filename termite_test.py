from go import bytes, os, io, io/ioutil
from go import mime/multipart, net/http
from go import encoding/base64
from go import path/filepath as FP
from . import A, au, bundle, keyring, launch, sym, util

Ring = None

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

def LoadTermite(i, t3_rpc):
  say i
  for cmd in ['BigLocalDir', 'BigRemoteDir', 'SPush', 'BigLocalDir', 'BigRemoteDir']:
    say '@@@@@@@@@@@@@@@@@@@@@@@@@ Building:', i, cmd
    # bund = 'termite%d' % i if i<3 else 'termite%dpeek' % i
    bund = 'termite%d' % i
    pw = 'password' if i>2 else ''
    fullcmd = [
        '--bund=%s' % bund, '--dir=./__termite_local', '--server=127.0.0.1:%s' % t3_rpc,
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

def main(args):
  global Ring

  keyring.RingFilename.X = 'termite.ring'
  Clear()
  quit = rye_chan(1)

  t1 = launch.Aphid(quit=quit, filename='termite.laph:job:termite11')
  t2 = launch.Aphid(quit=quit, filename='termite.laph:job:termite12')
  t3 = launch.Aphid(quit=quit, filename='termite.laph:job:termite13')
  t1_http = t1.laph.Eval('/job:termite11/ports/http')
  say t1_http
  t3_rpc = t3.laph.Eval('/job:termite13/ports/rpc')
  say t3_rpc

  say t1
  say t2
  say t3

  t3.StartAll()
  Ring = t3.ring

  bt2 = t3.bundles['termite2']
  say bt2, bt2.bundir
  bundle.WriteFile(bt2, 'abcde/lmnop/wxyz.txt', 'oscar meyer wiener')
  say 'Wrote it'
  x = bundle.ReadFile(bt2, 'abcde/lmnop/wxyz.txt')
  say 'Red it', x

  A.Sleep(1)
  LoadTermite(0, t3_rpc=t3_rpc)

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
    LoadTermite(i, t3_rpc=t3_rpc)
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
      url='http://localhost:%s/@termite1.formic/*attach_media_submit?' % t1_http,
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
  z1 = HttpMethod('POST', 'http://localhost:%s/@termite1.formic/*edit_page_submit?' % t1_http, body=body, pw='password')
  say z1

  # Get the home page.
  A.Sleep(1)
  z2 = HttpMethod('GET', 'http://localhost:%s/@termite1.formic/home?' % t1_http, body='', pw='password')
  say z2

  say "OKAY termite_test.py"

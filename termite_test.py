from go import bytes, os, io, io/ioutil
from go import mime/multipart, net/http
from go import encoding/base64
from go import path/filepath as FP
from . import A, au, bundle, flag, keyring, launch, sym, util

Ring = None

def ClearAndInitSubdirectories():
  for d in ['__termite_local', '__termite__termite11', '__termite__termite12', '__termite__termite13']:
    os.RemoveAll(d)
    os.Mkdir(d, 0777)
    if not d.endswith('local'):
      for b in ['b.termite0', 'b.termite1', 'b.termite2', 'b.termite3']:
        os.Mkdir(FP.Join(d, b), 0777)
    else:
      # termite3peek (sym) is a dup of termite3 (websym)
      os.Symlink('b.termite3', FP.Join(d, 'b.termite3peek')) 

  os.MkdirAll('__termite_local/termite0/dns', 0777)
  ioutil.WriteFile(
      '__termite_local/termite0/dns/aphid.cc',
      'aphid.cc. IN A 127.0.0.1\n',
      0666)
  jpg = ioutil.ReadFile('termite.jpg')
  os.MkdirAll('__termite_local/termite0/web/media', 0777)
  ioutil.WriteFile('__termite_local/termite0/web/media/termite.jpg', jpg, 0666)

def Cmp(file1, file2):
  """Assert the contents of two named files are equal."""
  say file1
  say file2
  x1 = ioutil.ReadFile(file1)
  x2 = ioutil.ReadFile(file2)
  say len(x1), len(x2)
  must x1 == x2

def Glob1(*names):
  """Join and Glob and assert exactly 1 result."""
  say names
  vec = FP.Glob(FP.Join('.', *names))
  say names, vec
  must len(vec) == 1
  return vec[0]

def PushLocalToTermiteBundle(i, t3_rpc):
  say i
  for cmd in ['BigLocalDir', 'BigRemoteDir', 'SPush', 'SLEEP', 'BigLocalDir', 'BigRemoteDir']:
    if cmd == 'SLEEP':
      say 'LLLLLL Sleeping', 1
      A.Sleep(1)
    else:
      say 'LLLLLL Building:', i, cmd
      bund = 'termite%d' % i
      pw = 'password' if i>2 else ''
      fullcmd = [
          '--bund=%s' % bund, '--dir=./__termite_local', '--server=127.0.0.1:%s' % t3_rpc,
          '--cid=91', '--sid=92', '--exit=0', '--pw=%s' % pw,
          cmd]
      say 'LLLLLL Running:', i, fullcmd
      au.main(fullcmd)
      say 'LLLLLL Ran:', i

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

SLEEP = flag.Int('sleep', 1, 'Extra final sleep time')

def main(args):
  global Ring
  args = flag.Munch(args)

  # We will need keys for sym & websym bundles.
  keyring.RingFilename.X = 'termite.ring'
  # Must load zone 'aphid.cc' from Seed Dir before starting Aphids.
  launch.SEEDDIR.X = 'termite.seed'

  ClearAndInitSubdirectories()
  quit = rye_chan(1)

  t1 = launch.Aphid(quit=quit, filename='termite.laph:job:termite11')
  t2 = launch.Aphid(quit=quit, filename='termite.laph:job:termite12')
  t3 = launch.Aphid(quit=quit, filename='termite.laph:job:termite13')
  t3.StartAll()

  t1_http = t1.laph.EvalPath('/job:termite11/ports/http')
  say t1_http
  t3_rpc = t3.laph.EvalPath('/job:termite13/ports/rpc')
  say t3_rpc
  Ring = t3.ring

  a3_b2 = t3.bundles['termite2']
  say a3_b2, a3_b2.bundir
  bundle.WriteFile(a3_b2, 'abcde/lmnop/wxyz.txt', 'oscar meyer wiener')
  say 'Wrote it'
  x = bundle.ReadFile(a3_b2, 'abcde/lmnop/wxyz.txt')
  say 'Red it', x

  A.Sleep(1)
  PushLocalToTermiteBundle(0, t3_rpc=t3_rpc)

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
    PushLocalToTermiteBundle(i, t3_rpc=t3_rpc)
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

  # Install a template for /formic/layouts/_default/single.html
  buf = bytes.NewBuffer('<html><body>Default Single Template: (((Title: {{$.Title}})))</body></html>\n')
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
  must z2 == byt("<html><body>Default Single Template: (((Title: HomePage)))</body></html>\n")

  say "OKAY termite_test.py"
  A.Sleep(SLEEP.X)

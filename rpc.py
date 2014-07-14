go import fmt
go import html
go import net/http
go import net/url
go import time
go import io/ioutil

def Double(x):
  return x + x

def Echo(w, r):
  try:
    fmt.Fprintf(w, "Hello Foo, %q", html.EscapeString(r.URL.Path))
  except as ex:
    print "Echo Exception:", ex

class RpcFunc:
  def __init__(self, fn):
    self.fn = fn
  def Call(self, w, r):
    r.ParseForm()
    data = ''
    vec = r.PostForm.get('data')
    if vec:
      data = vec[0]
    print "data:", repr(data)
    self.fn(w, r)

  def Invoke(self, w, r):
    r.ParseForm()
    arg = None
    vec = r.PostForm.get('data')
    if vec:
      arg = unpickle(vec[0])
    print "arg <<<", arg
    z = self.fn(arg)
    print "z >>>", z
    w.Write(pickle(z))

def Register(name, fn):
    http.HandleFunc('/APHID_RPC/' + name, RpcFunc(fn).Call)
    
def RegisterP(name, fn):
    http.HandleFunc('/APHID_RPC/' + name, RpcFunc(fn).Invoke)

def GoListenAndServe(hp):
  z = http.ListenAndServe(hp, None)
  yield ('Never', z)

def Run():
  d = { 'data': [pickle(1234)] }
  form = gocast(url.Values, d)
  resp = http.PostForm("http://localhost:8080/APHID_RPC/Double", form)
  print '>>>>resp>>>>>>', repr(resp)
  body = ioutil.ReadAll(resp.Body)
  print '>>>>body>>>>>>', repr(body)
  print '>>>>body>>>>>>', unpickle(body)
  resp.Body.Close()

    
def main(argv):
  Register('Echo', Echo)
  RegisterP('Double', Double)
  z = GoListenAndServe(':8080')
  time.Sleep(100 * time.Millisecond)
  Run()

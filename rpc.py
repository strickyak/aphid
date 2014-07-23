from go import io/ioutil
from go import net/http
from go import net/url
from go import regexp

MAGIC_PATH = 'AphiD_RpC1'

PARSE_HP = regexp.MustCompile('^([-A-Za-z0-9.]+)[:]([0-9]+)$')

class RpcFunc:
  def __init__(self, fn):
    self.fn = fn

  def Call1(self, w, r):
    r.ParseForm()
    pickles = r.PostForm.get('pickle')
    if not pickles:
      w.WriteHeader(http.StatusExpectationFailed)
      w.Write('Missing RPC form field "pickle"')

    try:
      say len(pickles)
      say len(pickles[0])
      arg = unpickle(pickles[0])
      say arg
      z = self.fn(arg)
      say z
      p = pickle(z)
      say repr(p)
      say unpickle(p)
      say w.Write(p)
      say unpickle(p)
      say 'OKAY -- Written'
    except as ex:
      w.WriteHeader(http.StatusInternalServerError)
      w.Write('ERROR CAUGHT: ' + ex)

class Dial:
  def __init__(self, host_port):
    hp = PARSE_HP.FindStringSubmatch(host_port)
    if not hp:
      raise 'Bad Host:Port spec: ' + host_port
    _, self.host, self.port = hp

  def Register(self, name, fn):
    http.HandleFunc('/' + MAGIC_PATH + '/' + name, RpcFunc(fn).Call1)

  def GoListenAndServe(self):
    hp = "%s:%s" % (self.host, self.port)
    http.ListenAndServe(hp, None)
    yield 'NOT_REACHED'

  def Call1(self, rpc_name, arg):
    say arg
    d = { 'pickle': [pickle(arg)] }
    say d
    uri = "http://%s:%s/%s/%s" % (self.host, self.port, MAGIC_PATH, rpc_name)
    response = http.PostForm(uri, gocast(url.Values, d))
    body = ioutil.ReadAll(response.Body)
    response.Body.Close()
    if response.StatusCode != 200:
      raise 'In RPC %q: ERROR %d: %q' % (rpc_name, response.StatusCode, body) 
    z = unpickle(body)
    return z

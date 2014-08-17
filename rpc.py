from go import io/ioutil
from go import net/http
from go import net/url
from go import regexp

MAGIC_PATH = 'AphiD_RpC1'

PARSE_HP = regexp.MustCompile('^([-A-Za-z0-9.]+)[:]([0-9]+)$')

class RpcFunc:
  def __init__(self, fn):
    self.fn = fn

  def Request(self, w, r):
    r.ParseForm()
    pickles = r.PostForm.get('pickle')
    if not pickles:
      w.WriteHeader(http.StatusExpectationFailed)
      w.Write('Missing RPC form field "pickle"')
    return unpickle(pickles[0])

  def Respond(self, w, r, z):
      w.Write(pickle(z))

  def RespondError(self, r, w, ex):
      w.WriteHeader(http.StatusInternalServerError)
      w.Write('%s' % ex)

  def Call1(self, w, r):
    try:
      a1 = self.Request(w, r)
      z = self.fn(a1)
      self.Respond(w, r, z)
    except as ex:
      self.RespondError(r, w, ex)

  def Call2(self, w, r):
    try:
      a1, a2 = self.Request(w, r)
      z = self.fn(a1, a2)
      self.Respond(w, r, z)
    except as ex:
      self.RespondError(r, w, ex)

  def Call3(self, w, r):
    try:
      a1, a2, a3 = self.Request(w, r)
      z = self.fn(a1, a2, a3)
      self.Respond(w, r, z)
    except as ex:
      self.RespondError(r, w, ex)

class Dial:
  def __init__(self, host_port):
    hp = PARSE_HP.FindStringSubmatch(host_port)
    if not hp:
      raise 'Bad Host:Port spec: ' + host_port
    _, self.host, self.port = hp

  def Register1(self, name, fn):
    http.HandleFunc('/' + MAGIC_PATH + '/' + name, RpcFunc(fn).Call1)

  def Register2(self, name, fn):
    http.HandleFunc('/' + MAGIC_PATH + '/' + name, RpcFunc(fn).Call2)

  def Register3(self, name, fn):
    http.HandleFunc('/' + MAGIC_PATH + '/' + name, RpcFunc(fn).Call3)

  def ListenAndServe(self):
    hp = "%s:%s" % (self.host, self.port)
    http.ListenAndServe(hp, None)

  def Call1(self, rpc_name, a1):
    d = { 'pickle': [pickle(a1)] }
    uri = "http://%s:%s/%s/%s" % (self.host, self.port, MAGIC_PATH, rpc_name)
    response = http.PostForm(uri, gocast(url.Values, d))
    body = ioutil.ReadAll(response.Body)
    response.Body.Close()
    if response.StatusCode != 200:
      raise '%s\n  -- in RPC %q\n  -- http code %d\n  -- uri %q' % (body, rpc_name, response.StatusCode, uri)
      raise 'In RPC %q: ERROR %d: %q' % (rpc_name, response.StatusCode, body) 
    z = unpickle(body)
    return z

  def Call2(self, rpc_name, a1, a2):
    d = { 'pickle': [pickle((a1, a2))] }
    uri = "http://%s:%s/%s/%s" % (self.host, self.port, MAGIC_PATH, rpc_name)
    response = http.PostForm(uri, gocast(url.Values, d))
    body = ioutil.ReadAll(response.Body)
    response.Body.Close()
    if response.StatusCode != 200:
      raise '%s\n  -- in RPC %q\n  -- http code %d\n  -- uri %q' % (body, rpc_name, response.StatusCode, uri)
      raise 'In RPC %q: ERROR %d: %q' % (rpc_name, response.StatusCode, body) 
    z = unpickle(body)
    return z

  def Call3(self, rpc_name, a1, a2, a3):
    d = { 'pickle': [pickle((a1, a2, a3))] }
    uri = "http://%s:%s/%s/%s" % (self.host, self.port, MAGIC_PATH, rpc_name)
    response = http.PostForm(uri, gocast(url.Values, d))
    body = ioutil.ReadAll(response.Body)
    response.Body.Close()
    if response.StatusCode != 200:
      raise '%s\n  -- in RPC %q\n  -- http code %d\n  -- uri %q' % (body, rpc_name, response.StatusCode, uri)
      raise 'In RPC %q: ERROR %d: %q' % (rpc_name, response.StatusCode, body) 
    z = unpickle(body)
    return z

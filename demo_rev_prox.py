# rye run demo_rev_prox.py -- -target='http://localhost:8080/Pre/Fix/?abc=123&xyz=789' --port=:8088
# rye run demo_web_echo.py
#   http://localhost:8080/foo/bar?color=red
#   http://localhost:8088/foo/bar?color=red

from go import net/http
from go import net/http/httputil
from go import net/url
from . import A
from . import flag

TARGET = flag.String('target', '', 'Target URL')
PORT = flag.String('port', ':8080', 'Listen on this ":port"')

def main(args):
  args = flag.Munch(args)

  rev = httputil.NewSingleHostReverseProxy(url.Parse(TARGET.X))
  http.Handle('/', rev)

  http.ListenAndServe( PORT.X , None )

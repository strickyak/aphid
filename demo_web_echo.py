# rye run demo_web_echo.py

from go import net/http
from go import net/http/httputil
from go import fmt
from . import flag

def WebEcho(w, r):
  w.Header().Set('Content-Type', 'text/plain')

  try:
    fmt.Fprintf(w, "URL.Scheme: %q\n", r.URL.Scheme)
    fmt.Fprintf(w, "URL.Host: %q\n", r.URL.Host)
    fmt.Fprintf(w, "URL.Path: %q\n", r.URL.Path)
    fmt.Fprintf(w, "Method: %q\n", r.Method)
    fmt.Fprintf(w, "Proto: %q\n", r.Proto)
    fmt.Fprintf(w, "Host: %q\n", r.Host)
    fmt.Fprintf(w, "ContentLength: %d\n", r.ContentLength)
    fmt.Fprintf(w, "TransferEncoding: %v\n", r.TransferEncoding)
    fmt.Fprintf(w, "RemoteAddr: %q\n", r.RemoteAddr)
    fmt.Fprintf(w, "RequestURI: %q\n", r.RequestURI)

    for k, v in r.Header.items():
      fmt.Fprintf(w, "header: %q = %q\n", k, v)

    r.ParseForm()
    for k, v in r.Form.items():
      fmt.Fprintf(w, "form: %q = %q\n", k, v)

    fmt.Fprintf(w, "\n***\nDumpRequest:\n%s\n***\n", httputil.DumpRequest(r, True))
    fmt.Fprintf(w, "END.")

  except as ex:
    w.Write( 'Exception:\n%s\n' % ex)

PORT = flag.String('port', ':8080', 'Listen on this ":port"')

def main(args):
  args = flag.Munch(args)
  http.HandleFunc('/', WebEcho)
  http.ListenAndServe( PORT.X , None )

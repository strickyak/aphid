from go import net/http
from go import fmt

def WebEcho(w, r):
  w.Header().Set('Content-Type', 'text/plain')

  try:
    fmt.Fprintf(w, "Path: %q\n", r.URL.Path)
    fmt.Fprintf(w, "Proto: %q\n", r.Proto)

    for k in r.Header:
      fmt.Fprintf(w, "header: %q\n", k)

    r.ParseForm()
    for k, v in r.Form.items():
      fmt.Fprintf(w, "form: %q = %q\n", k, v)

    fmt.Fprintf(w, "END.")

  except as ex:
    w.Write( 'Exception:\n%s\n' % ex)

  return

def main(_):
  http.HandleFunc('/', WebEcho)
  http.ListenAndServe( ':8080' , None )

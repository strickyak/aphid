#from . import among, aweber, awiki, awedit, azoner, formic, smilax4, stash
#from . import bundle, keyring, laph3, pubsub, rbundle, util
from go import bufio, fmt, html, io/ioutil, net/http, os, regexp, time
from go import path as P, path/filepath as F
#from rye_lib import data

Esc = html.EscapeString

MATCH_REFERER = regexp.MustCompile('^[^?]+(/@[-A-Za-z0-9_]+)(/.*)$').FindStringSubmatch

class AMux:
  def __init__():
    .mux = http.NewServeMux()
    .mux.HandleFunc('/', .Otherwise)
    .paths = {}

  def HandleFunc(path, func):
    if '/' not in path:
      path += '/'
    .mux.HandleFunc(path, func)
    .paths[path] = func

  def PrefiRestF(w, r, target):
    """Returns "/@prefi" (if needed), rest of path,  and HandlerFunc."""
    # We say Prefi instead of Prefix because the final '/' is removed.
    m = MATCH_REFERER(target)
    # If the target already has /@prefix/ in it, we don't need this.
    if not m:
      referer = r.Header.Get('Referer')
      say referer
      if referer:
        say referer, True
        m = MATCH_REFERER(referer)
        say referer, m
        if m:
          _, r_prefi, r_rest = m
        say referer, r_prefi, r_rest
        if r_prefi:
          say sorted(.paths.keys())
          f = .paths.get(r_prefi + '/')
          say referer, r_prefi, target, f
          if f:
            return r_prefi, target, f
    say referer, None
    return '', target, None

  def SmartRedirect(w, r, dest):
    raise 'zork'
    prefi, rest, f = .PrefiRestF(w, r, dest)
    if prefi:
      # Add the prefix.
      dest2 = '%s%s' % (prefi, rest)
      return http.Redirect(w, r, dest2, http.StatusTemporaryRedirect)
    else:
      # Prefixing not required.
      return http.Redirect(w, r, dest, http.StatusTemporaryRedirect)

  def Otherwise(w, r):
    must r.URL.Path.startswith('/'), 'Weird URL.Path: %q' % r.URL.Path
    say r.URL.Scheme, r.URL.Host, r.URL.Path, r.URL.RawQuery
    prefi, rest, f = .PrefiRestF(w, r, r.URL.Path)
    say prefi, rest, f
    if prefi:
      # We can redirect a GET to the dest url with the proper prefix.
      if r.Method == 'GET':
        say 'http.Redirect', w, r, prefi, rest, r.URL.RawQuery, http.StatusTemporaryRedirect
        return http.Redirect(w, r, '%s%s?%s' % (prefi, rest, r.URL.RawQuery), http.StatusTemporaryRedirect)

      # For posts, we call the function, and let them do smarter .SmartRedirect(w, r, dest) above.
      if f:
        return f(w, r)

    # Emit consolation message with links to active /@prefixes
    w.Header().Set('Content-Type', 'text/html; charset=UTF-8')
    w.WriteHeader(http.StatusNotFound)
    try:
      fmt.Fprintf(w, Esc("404 NOT FOUND (Path prefix not registered)\n\n") + '<br><p>')
      fmt.Fprintf(w, Esc("[aphid] Proto: %q Method: %q\n" % ( r.Proto, r.Method)) + '<br><p>')
      fmt.Fprintf(w, Esc("[aphid] Host: %q Path: %q\n" % (r.Host, r.URL.Path)) + '<br><p>')
      for k, v in sorted(r.Header.items()):
        for e in v:
          fmt.Fprintf(w, Esc("[aphid] Header: %q : %q\n" % (k, e)) + '<br>')
      fmt.Fprintf(w, '<br><p>')

      fmt.Fprintf(w, 'Are you looking for one of these?<ul>')
      for k in sorted(.paths.keys()):
        if k.startswith('/'):
          fmt.Fprintf(w, '<li> <a href="%s">%s</a>', k, Esc(k))
        else:
          fmt.Fprintf(w, '<li> <a href="http://%s">%s</a>', k, Esc(k))
      fmt.Fprintf(w, '</ul>')
    except as ex:
      fmt.Fprintf(w, '<br><br><tt>******* EXCEPTION ******* %s' % Esc(str(ex)))

pass

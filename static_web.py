from go import html
from go import net/http
from go import os
from go import regexp
from go import strings
from . import flag
from . import eval

SLASHDOT = regexp.MustCompile('(^|[/])[.]')

def EmitDir(w, r, fd, prefix, path):
  names = fd.Readdirnames(-1)
  w.Write('<html><body><h3>Directory %s</h3> <ul>\n' % path)
  for name in names:
    name = html.EscapeString(name)
    w.Write('<li><a href="%s">%q</a></li>\n' % (name, name))
  w.Write('</ul>\n')

def FileExists(filename):
  try:
    z = not os.Stat(filename).IsDir()
    say 'FileExists?', filename, z
    return z
  except as err:
    say 'FileExists --> ', err
    return False

def WebFunc(w, r):
  path = r.URL.Path
  try:
    hostdir = WEB_MAP.get(r.Host)
    if not hostdir:
      hostdir = WEB_MAP.get(strings.Split(r.Host, ':')[0])
    say WEB_MAP, hostdir
    must hostdir, "Could not find host directory: %q" % r.Host

    filename = "/%s/%s/%s" % (ROOT.X, hostdir, path)
    if SLASHDOT.FindString(filename):  # Subvert /.. and dotfiles.
      raise 'Bad Filename', filename

    fd = os.Open(filename)
    with defer fd.Close():
      st = fd.Stat()
      if st.IsDir():
        if path[-1] != '/':
          http.Redirect(w, r, path + '/', http.StatusMovedPermanently)
        elif FileExists(filename + 'index.html'):
          say "SERVING INDEX", filename + 'index.html'
          fd = os.Open(filename + 'index.html')
          with defer fd.Close():
            http.ServeContent(w, r, filename + 'index.html', st.ModTime(), fd)
        else:
          EmitDir(w, r, fd, '/', path)
      else:
        say "SERVING FILE", filename
        http.ServeContent(w, r, filename, st.ModTime(), fd)

  except as ex:
    w.Header().Set('Content-Type', 'text/plain')
    w.Write( 'Exception:\n%s\n' % ex)

ROOT = flag.String('root', '/tmp', 'Root of serving dirs.')
PORT = flag.String('port', 8080, 'Port to serve on.')
MAP = flag.String('map', '{"localhost":"localhost"}', 'Dict mapping Host to subdir name.')
WEB_MAP = {}

def main(argv):
  global WEB_MAP
  argv = flag.Munch(argv)
  WEB_MAP = eval.Eval(MAP.X)
  say MAP.X, WEB_MAP
  http.HandleFunc('/', WebFunc)
  http.ListenAndServe( ':' + PORT.X , None )

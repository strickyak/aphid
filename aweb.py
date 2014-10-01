from go import net/http
from go import regexp
from go import strings
from . import afs

WEB_ROOT = '/Here/webroot'
WEB_MAP = { 'localhost:8080': 'local', 'yak.net': 'yak', }

SLASHDOT = regexp.MustCompile('[/][.]')

def EmitDir(w, r, fd, prefix, path):
  names = fd.Readdirnames(-1)
  w.Write('<html><body><h3>Directory %s</h3> <ul>\n' % path)
  for name in names:
    # TODO: escape correctly.
    w.Write('<li><a href="%s">%q</a></li>\n' % (name, name))
  w.Write('</ul>\n')

def WebFunc(w, r):
  say r.Header
  path = r.URL.Path

  try:
    hostdir = WEB_MAP.get(r.Host)
    if not hostdir:
      hostdir = WEB_MAP.get(strings.Split(r.Host, ':')[0])

    filename = "/%s/%s/%s" % (WEB_ROOT, hostdir, path)
    if SLASHDOT.FindString(filename):  # Subvert /.. and dotfiles.
      raise 'slashdot not allowed in filename: %q' % filename

    fd = afs.Open(filename)
    defer fd.Close()
    st = fd.Stat()
    if st.IsDir():
      if path[-1] == '/':
        EmitDir(w, r, fd, '/', path)
      else:
        http.Redirect(w, r, path + '/', http.StatusMovedPermanently)
    else:
      http.ServeContent(w, r, path, st.ModTime(), fd)

  except as ex:
    w.Header().Set('Content-Type', 'text/plain')
    w.Write( 'Exception:\n%s\n' % ex)

http.HandleFunc('/', WebFunc)

http.ListenAndServe( ':8080' , None )

from go import net/http
from go import strings
from go import os
from go import io/ioutil

WEB_ROOT = '/home/strick/webroot'
WEB_MAP = { 'localhost:8080': 'local', 'yak.net': 'yak', }

def WebFunc(w, r):
  say r.Header
  # path = strings.Split(r.URL.Path, '/')
  path = r.URL.Path

  try:
    w.Header().Set('Content-Type', 'text/html')
    w.Write('<html><body>\n')
    w.Write('path: %s<p>\n' % path)
    w.Write('host: %s<p>\n' % r.Host)
    w.Write('Header: %s<p>\n' % repr(r.Header))
    w.Write('r: %s<p>\n' % repr(r))

    hostdir = WEB_MAP.get(r.Host)
    if not hostdir:
      hostdir = WEB_MAP.get(strings.Split(r.Host, ':')[0])

    filename = "/%s/%s/%s" % (WEB_ROOT, hostdir, path)
    fd = os.Open(filename)
    st = fd.Stat()
    if st.IsDir():
      names = fd.Readdirnames(-1)
      w.Write('\n<h3>Directory %s</h3> <ul>\n' % path)
      for name in names:
        w.Write('<li>%s</li>\n' % name)
      w.Write('</ul>\n')

    else:
      contents = ioutil.ReadAll(fd)
      fd.Close()
      w.Write('\n<listing>\n')
      w.Write(contents)
      w.Write('\n</listing>\n')

  except as ex:
    w.Header().Set('Content-Type', 'text/plain')
    w.Write( 'Exception:\n%s\n' % ex)

http.HandleFunc('/', WebFunc)

http.ListenAndServe( ':8080' , None )

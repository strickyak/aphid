from go import bytes, html, os, regexp
from go import net/http
from go import path/filepath

from . import bundle, flag
from . import awiki

BIND = flag.String('bind_addr', ':8080', 'Bind to this address to server web.')

IS_EVIL_PATH = regexp.MustCompile('(^|[/])[.]').FindString
MATCH_HOST_IN_PATH = regexp.MustCompile('/@([-A-Za-z0-9.]+)@($|/.*$)').FindStringSubmatch
IS_DOMAIN = regexp.MustCompile('^[-a-z0-9.]+$').FindString

def EmitDir(w, r, fd, prefix, path):
  names = fd.Readdirnames(-1)
  w.Write('<html><body><h3>Directory %s</h3> <ul>\n' % path)
  for name in names:
    name = html.EscapeString(name)
    w.Write('<li><a href="%s">%q</a></li>\n' % (name, name))
  w.Write('</ul>\n')

def EmitBundDir(w, r, prefix, path, names):
  w.Write('<html><body><h3>Directory %s</h3> <ul>\n' % path)
  for name in names:
    name = html.EscapeString(name)
    name = ''.join( [('_' if c == '@' else c) for c in name] )
    w.Write('<li><a href="./%s">%q</a></li>\n' % (name, name))
  w.Write('</ul>\n')

def DirExists(filename):
  try:
    return os.Stat(filename).IsDir()
  except:
    return False

def FileExists(filename):
  try:
    return not os.Stat(filename).IsDir()
  except:
    return False

class WebDir:
  def __init__(top):
    .top = top

  def Handle4(w, r, host, path):
    filename = filepath.Join(.top, path)
    try:
      if DirExists(filename):
        if path[-1] != '/':
          http.Redirect(w, r, r.URL.Path + '/', http.StatusMovedPermanently)
          return

      http.ServeFile(w, r, filename)
      return

      fd = os.Open(filename)
      with defer fd.Close():
        st = fd.Stat()
        if st.IsDir():
          if path[-1] != '/':
            # TODO -- needs to correct original path.
            http.Redirect(w, r, path + '/', http.StatusMovedPermanently)
          else:
            index_path = filepath.Join(filename, 'index.html')
            if FileExists(index_path):
              say "SERVING INDEX", index_path
              fd = os.Open(index_path)
              with defer fd.Close():
                http.ServeContent(w, r, index_path, st.ModTime(), fd)
            else:
              EmitDir(w, r, fd, '/', path)
        else:
          say "SERVING FILE", filename
          http.ServeContent(w, r, filename, st.ModTime(), fd)

    except as ex:
      w.Header().Set('Content-Type', 'text/plain')
      w.Write( 'Exception:\n%s\n' % ex)

class BundDir:
  def __init__(bund_name):
    .bund_name = bund_name
    .b = bundle.Bundles[bund_name]

  def Handle4(w, r, host, path):
    try:
      if path.endswith('/'):
        dd = sorted(.b.ListDirs(path))
        ff = sorted(.b.ListFiles(path))
        names = ["%s/" % d for d in dd] + ff
        EmitBundDir(w, r, None, path, names)

      else:
        isDir, modTime, size = .b.Stat3(path)
        if isDir:
          http.Redirect(w, r, path + '/', http.StatusMovedPermanently)

        br = bytes.NewReader(.b.ReadFile(path))  # TODO, avoid loading in memory?
        http.ServeContent(w, r, path, modTime, br)

    except as ex:
      w.Header().Set('Content-Type', 'text/plain')
      w.Write( 'Exception:\n%s\n' % ex)

def RoutingFunc(w, r):
  path = r.URL.Path
  host = r.Host
  say host, path
  try:
    # Subvert "." files and ".." directories
    if IS_EVIL_PATH(path):
      raise 'Bad Path: %q' % path

    # Perhaps extract an overriding Host from the path.
    m = MATCH_HOST_IN_PATH(path)
    if m:
      _, host2, path2 = m
      say host2, path2
      if not path2:  # Require a trailing '/' after the "/@@host":
        http.Redirect(w, r, '/@%s@/' % host2, http.StatusMovedPermanently)
        return
      host, path = host2, path2
      say host2, path2

    # Normalize the host, without post, to lowercase, using 'default' if it is missing (for HTTP/1.0).
    if not host:
      host = 'default'
    host = host.split(':')[0].lower()

    # Special "www." removal.
    if host.startswith('www.'):
      host = host[4:]

    # Lookup and call the host handler.
    fn = HostHandlers.get(host)
    say host, path, fn
    if not fn:
      raise 'Unknown host: %q; path: %q' % (host, path)

    # Call the handler
    fn(w, r, host, path)

  except as err:
    w.Header().Set('Content-Type', 'text/plain')
    w.Write('\n\nSorry, an error occurred in Aphid:\n\n%s\n' % err)

def RegisterDirectories(argv):
  for a in argv:
    must DirExists(a)
    base = filepath.Base(a)
    must IS_DOMAIN(base)
    HostHandlers[base] = WebDir(a).Handle4

def ProcessTriples():
  for name, d in flag.Triples.items():
    for k, v in d.items():
      if name == 'alias':
        h = HostHandlers.get(v)
        must h, 'Host %q not handled, in alias %q' % (v, k)
        HostHandlers[k] = h
      elif name == 'wiki':
        HostHandlers[k] = awiki.AWikiMaster(v).Handler4
      elif name == 'web':
        HostHandlers[k] = WebDir(v).Handle4
      elif name == 'web_bund':
        HostHandlers[k] = BundDir(v).Handle4
      else:
        raise 'Bad Triple name: %q' % name
  
HostHandlers = dict()

def main(argv):
  argv = flag.Munch(argv)
  bundle.LoadBundles(topdir='.')

  RegisterDirectories(argv)
  ProcessTriples()

  http.HandleFunc('/', RoutingFunc)
  http.ListenAndServe(BIND.X , None)

from go import bytes, html, os, regexp
from go import net/http
from go import path/filepath

from . import adapt, basic, bundle, flag
from . import awiki, util

BIND = flag.String('bind_addr', ':8080', 'Bind to this address to server web.')

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

STRIP_WEB = regexp.MustCompile('^/web($|/.*$)').FindStringSubmatch
def StripWeb(s):
  m = STRIP_WEB(s)
  return m[1] if m else s

class BundDir:
  def __init__(aphid, bund_name, bund=None):
    .aphid = aphid
    .bund_name = bund_name
    must bund
    .bund = bund

  def Handle2(w, r):
    host, extra, path, root = util.HostExtraPathRoot(r)
    say host, path
    return .Handle4(w, r, host, path)
  def Handle4(w, r, host, path):
    doDir = path.endswith('/')
    wpath = filepath.Join('/web', path)
    preLen = len('/web')
    say host, path, doDir, wpath

    if .bund.wx:
      user_pw = basic.GetBasicPw(w, r, .bund_name)
      if user_pw:
        user, pw = user_pw
      else:
        return  # We demanded Basic Authorization.

    try:
      say 'Link', pw
      .bund.Link(pw)
      with defer .bund.Unlink():
        if doDir:
          dd = sorted(.bund.ListDirs(wpath))
          ff = sorted(.bund.ListFiles(wpath))
          names = ["%s/" % x for x in dd] + [x for x in ff]
          say dd, ff, names
          EmitBundDir(w, r, None, path, names)

        else:
          isDir, modTime, size = .bund.Stat3(wpath)
          say isDir, modTime, size
          if isDir:
            http.Redirect(w, r, path + '/', http.StatusMovedPermanently)

          br = .bund.MakeReader(wpath, pw=pw, raw=False, rev=None)
          http.ServeContent(w, r, path, adapt.UnixToTime(modTime), br)

    except as ex:
      w.Header().Set('Content-Type', 'text/plain')
      w.Write( 'Exception:\n%s\n' % ex)
pass

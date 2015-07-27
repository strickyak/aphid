from go import bufio, bytes, fmt, log, reflect, regexp, sort, sync, time
from go import html/template, net/http, io, io/ioutil
from go import path as P
from go import crypto/sha256
from . import A, atemplate, bundle, dh, markdown, pubsub, util
from . import adapt, basic, flag
from lib import data

def Strip(s):
  return str(s).strip(' \t\n\r')

USERNAME_PAT = regexp.MustCompile('^[a-z0-9_]+$')
def MustUserName(s):
  if not USERNAME_PAT.FindString(s):
    raise 'Bad characters in username %q  (must be a-z 0-9 and _)' % s
  return s

ASCII_PAT = regexp.MustCompile('^[!-~]+$')
def MustAscii(s):
  if not ASCII_PAT.FindString(s):
    raise 'Bad characters in %q  (must be printable ascii)' % s
  return s

ASCII_SPACE_PAT = regexp.MustCompile('^[ !-~]+$')
def MustAsciiSpace(s):
  if not ASCII_SPACE_PAT.FindString(s):
    raise 'Bad characters in %q  (must be printable ascii or space)' % s
  return s

class StashMaster:
  def __init__(aphid, bname, bund, config):
    .mu = go_new(sync.Mutex)
    .aphid = aphid
    .bus = aphid.bus
    .bname = bname
    .bund = bund
    .mu = go_new(sync.Mutex)
    .LoadTemplates()
    .Reload()

  def LoadTemplates():
    .t = template.New('main')
    .t.Funcs(util.TemplateFuncs())
    .t.Parse(TEMPLATES)

  def Reload():
    .mu.Lock()
    with defer .mu.Unlock():
      .users = {}
      .meta = {}
      for fname in bundle.ListFiles(.bund, '/stash'):
        say fname
        if len(fname) > 5:
          name = fname[5:]
          fpath = '/stash/' + fname
          if fname.startswith('user.'):
            try:
              x = bundle.ReadFile(.bund, fpath)
              .users[name] = data.Eval(x)
            except as ex:
              log.Printf("Reload: Cannot read %q: %v", fpath, ex)
          if fname.startswith('meta.'):
            try:
              x = bundle.ReadFile(.bund, fpath)
              .meta[name] = data.Eval(x)
            except as ex:
              log.Printf("Reload: Cannot read %q: %v", fpath, ex)
      .Users = util.NativeMap(.users)
      .Meta = util.NativeMap(.meta)

  def Handle2(w, r):
    host, extra, path, base = util.HostExtraPathRoot(r)
    say host, extra, path, base

    try:
      return StashHandler(self, w, r, host, path, base)
    except as ex:
      say ex
      print >>w, '<br><br>\n\n*** ERROR *** <br><br>\n\n*** %s ***\n\n***' % ex
      raise ex
      return # raise ex

class StashHandler:
  def __init__(master, w, r, host, path, base):
    .master = master
    .w = w
    .r = r
    .host = host
    .path = path
    .base = base

    master.mu.Lock()
    with defer master.mu.Unlock():
      .d = dict(Users=master.Users, Meta=master.Meta,
                R=r, Host=host, Path=path, Base=base,
                Title='Stash of Files')

    realm = 'Stash-%s' % master.bund.bname
    username = '?'
    u = None
    if path != '/':
      try:
        username, pw = basic.GetBasicPw(w, r, realm)
        u = .master.users[username]
        h = '%x' % sha256.Sum256(Strip(pw))
        if h != u['pw']:
          raise 'Bad username %q or password %q' % (username, h)
        .d['User'] = username
        pass
      except as ex:
        log.Printf("BASIC AUTH: %q %v", username, ex)
        return basic.Fails(w, r, realm)

    .r.ParseForm()
    switch path:

      default:
        .Emit('HOME')

      case '/':
        .Emit('HOME')

      case '/list':
        z = {}
        for f in bundle.ListFiles(.master.bund, '/stash'):
          z[f] = f
        .d['Files'] = master.Meta
        .Emit('LIST')

      case '/view':
        fname = Strip(.r.Form['f'][0])
        .d['Title'] = 'File: %q' % fname
        .d['Text'] = bundle.ReadFile(.master.bund, '/stash/data.' + fname)
        .Emit('VIEW')

      case '/add_user':
        if not u.get('admin'):
          raise 'Cannot add user: You are not an admin.'
        .Emit('ADD_USER')

      case '/submit_add_user':
        say '%v' % .r.Form
        say .r.Form.keys()
        say .r.Form.items()
        say '%v' % .r.PostForm
        say .r.PostForm.keys()
        say .r.PostForm.items()
        u2 = MustUserName(Strip(.r.PostForm['new_user_name'][0]))
        f2 = MustAsciiSpace(Strip(.r.PostForm['new_full_name'][0]))
        p2 = MustAsciiSpace(Strip(.r.PostForm['new_passwd'][0]))
        a2 = MustAscii(Strip(.r.PostForm['new_admin'][0]))
        h2 = '%x' % sha256.Sum256(p2)
        dh2 = dh.Forge(u2, f2, dh.GROUP)

        j = repr(dict(
                 fullname=f2,
                 pw=h2,
                 admin=a2.lower().startswith('y'),
                 public=dh2.Public(),
                 secret=dh2.Secret()
                 ))
        if .master.users.get(u2):
          raise 'User %q already exists.' % u2

        bundle.WriteFile(.master.bund, '/stash/user.%s' % u2, j)
        .master.Reload()
        http.Redirect(w, r, '%s/list' % .base, http.StatusTemporaryRedirect)

  def Emit(tname):
    .d['All'] = repr(.d)
    .master.t.ExecuteTemplate(.w, tname, util.NativeMap(.d))

TEMPLATES = `
{{define "HEAD"}}
  <html><head>
    <title>{{.TItle}}</title>
  </head><body>
    <h2>{{.Title}}</h2>
    <p>ALL = {{.All}}
    <p>
{{end}}

{{define "TAIL"}}
  </body></html>
{{end}}

{{define "HOME"}}
  {{ template "HEAD" $ }}
    Until we implement login,
    you can <a href="{{$.Base}}list">list</a> all files.
  {{ template "TAIL" $ }}
{{end}}

{{define "LIST"}}
  {{ template "HEAD" $ }}
    <b>Users:</b>
    <ul>
      {{ range $.Users | KV }}
        <li> <b>{{.K}}:</b> {{.V.fullname}}: {{.V}}
      {{ else }}
        <li> (There are no users.)
      {{ end }}
    </ul>
    <b>Files:</b>
    <ul>
      {{ range $.Files | KV }}
        <li> <a href="{{$.Base}}view?f={{.K}}">{{.K}}</a>
      {{ else }}
        <li> (There are no files.)
      {{ end }}
    </ul>
  {{ template "TAIL" $ }}
{{end}}

{{define "VIEW"}}
  {{ template "HEAD" $ }}
    <div class="Text">
      <pre>{{ .Text }}</pre>
    </div>
  {{ template "TAIL" $ }}
{{end}}

{{define "ADD_USER"}}
  {{ template "HEAD" $ }}
    <div class="Form">
      <form method="POST" action="{{$.Base}}submit_add_user">
        Create a new user:
        <p>
        User Name: &nbsp; <input type=text size=20 name=new_user_name>
        <p>
        Full Name: &nbsp; <input type=text size=80 name=new_full_name>
        <p>
        Password: &nbsp; <input type=text size=24 name=new_passwd>
        <p>
        Admin: &nbsp; <input type=text size=5 name=new_admin value="no">
        <p>
        <input type=submit name=submit value=Save> &nbsp; &nbsp;
        <input type=submit name=submit value=Cancel> &nbsp; &nbsp;
      </form>
    </div>
  {{ template "TAIL" $ }}
{{end}}
`

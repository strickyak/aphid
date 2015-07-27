from go import bufio, bytes, fmt, log, reflect, regexp, sort, sync, time
from go import html/template, net/http, io, io/ioutil
from go import path as P
from go import crypto/sha256
from . import A, atemplate, bundle, dh, markdown, pubsub, util
from . import adapt, basic, flag
from lib import data

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
    if path != '/':
      try:
        username, pw = basic.GetBasicPw(w, r, realm)
        u = .master.users[username]
        h = sha256.Sum256(pw.strip(' \t\n\r'))
        if ('%x' % h) != u['pw']:
          raise 'Bad username %q or password %q' % (username, h)
        .d['User'] = username
        pass
      except as ex:
        log.Printf("BASIC AUTH: %q %v", username, ex)
        return basic.Fails(w, r, realm)

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
        .r.ParseForm()
        fname = str(.r.Form['f'][0])
        .d['Title'] = 'File: %q' % fname
        .d['Text'] = bundle.ReadFile(.master.bund, '/stash/data.' + fname)
        .Emit('VIEW')

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
    you can <a href="{{$.Base}}/list">list</a> all files.
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
        <li> <a href="{{$.Base}}/view?f={{.K}}">{{.K}}</a>
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
`

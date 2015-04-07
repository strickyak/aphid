from go import bufio, bytes, fmt, reflect, regexp, sort, time
from go import html/template, net/http, io/ioutil
from go import path as P
from . import A, atemplate, bundle, markdown, util
from . import basic, flag
from lib import data

F = fmt.Sprintf
J = P.Join

MatchStatic = regexp.MustCompile('^/+(css|js|img|media)/(.*)$').FindStringSubmatch
MatchSimplePage = regexp.MustCompile('^/+(\\w+)/*$').FindStringSubmatch
MatchHome = regexp.MustCompile('^/+(index.html)?$').FindStringSubmatch
MatchCommand = regexp.MustCompile('^/+[*](\\w+)$').FindStringSubmatch

def Page():
  return dict(
    Title='PageTitle',
    Content='PageContent',
    )

class AFugioMaster:
  def __init__(aphid, bname, bund=None, users=None):
    .aphid = aphid
    .bname = bname
    must bund
    .bund = bund
    .users = users
    .ReloadTemplates()

  def ReloadTemplates():
    .t = template.New('ROOT')
    .t.Funcs(util.TemplateFuncs())

    try:
      dnames = bundle.ListDirs(.bund, '/fugio/layouts')
    except:
      dnames = []
    for dname in dnames:
      try:
        tnames = bundle.ListFiles(.bund, J('/fugio/layouts', dname))
      except:
        tnames = []
      for tname in tnames:
        if tname.endswith('.html'):
          name = J('theme', dname, tname)
          guts = bundle.ReadFile(.bund, J('/fugio/layouts', dname, tname))
          say name, guts
          .t.New(name).Parse(guts)

  def Handle2(w, r):
    host, extra, path, root = util.HostExtraPathRoot(r)
    say host, path
    try:
      return .Handle4(w, r, host, path)
    except as ex:
      say ex
      raise ex
  def Handle4(w, r, host, path):
    if path == '/favicon.ico':
      return

    m = MatchStatic(path)
    if m:
      flavor, path = m
      say 'MatchStatic', flavor, path
      rs, nanos, size = .bund.NewReadSeekerTimeSize('/fugio/static/%s/%s' % (flavor, path))
      http.ServeContent(w, r, r.URL.Path, time.Unix(0, nanos), rs)
      return

    # If not static, it must be a page.
    m = MatchSimplePage(path)
    if MatchHome(path):
      m = '/home', 'home'
    if m:
      _, page = m
      say 'MatchSimplePage', page
      w.Header().Set('Content-Type', 'text/html')

      md = bundle.ReadFile(.bund, '/fugio/content/%s.md' % page, None)
      say md
      front, html = markdown.Process(md)
      say front, html
      d = dict(Title=path, Content=html)
      say d
      util.NativeExecuteTemplate(.t, w, 'theme/_default/single.html', d)
      return

    m = MatchCommand(path)
    if m:
      _, cmd = m
      r.ParseForm()
      # Keep single-valued form fields for query.
      query = dict([(k, v[0]) for k, v in r.Form.items() if len(v)==1])
      switch cmd:
        case 'text':
          filepath = query['f']
          text = bundle.ReadFile(.bund, filepath, None)
          front, text = markdown.Process(text)
          front = str(front) if front else ''
          d = dict(Title='VIEW TEXT: %q' % filepath,
                   Edit='*edit?f=%s' % filepath,
                   Filepath=filepath,
                   Text=text,
                   Front=front,
                   )
        case 'edit':
          filepath = query['f']
          text = query.get('Text')
          if text:
            # This is a submission.
            bundle.WriteFile(.bund, filepath, text, None)
            http.Redirect(w, r, "*text?f=%s" % filepath, http.StatusMovedPermanently)
            return
          
          text = bundle.ReadFile(.bund, filepath, None)
          d = dict(Title='VIEW TEXT: %q' % filepath,
                   Edit='*edit?f=%s' % filepath,
                   Filepath=filepath,
                   Text=text,
                   EditTitle='Bogus Title for %q' % filepath
                   )
        default:
          raise "fugio: Bad cmd: %q %q %q" % (host, path, cmd)
      util.NativeExecuteTemplate(.t, w, cmd.upper(), d)
      return


    raise "fugio: Bad URL: %q %q" % (host, path)

HEAD = `
  <html><head>
    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
    <title>{{.Title}}</title>
    <style>
      body {
        background-color: #e5ccee;
      }
      .stuff {
        background-color: white;
        padding: 10px;
      }
      .floor {
        padding: 10px;
      }
    </style>
  </head><body>
    <table class="title-table" width=100% cellpadding=10><tr>
      <td align=center> <h2 class="title"><tt>{{.Title}}</tt></h2>
      <td align=right> <h2><tt>Fugio</tt></h2>
    </tr></table>
    <div class="stuff">
  `
TAIL = `
    </div>

    <hr>
    <tt><h4>DEBUG:</h4>
    <dl>
    {{ range (keys $) }}
      <dt> <b>{{ printf "%s:" . }}</b>
      <dd> {{ printf "%#v" (index $ .) }}
    {{ end }}
    </dl>
    </tt>

  </body></html>
  `
TEXT = `
  {{ template "HEAD" $ }}
  <pre>{{.Text}}</pre>
  </div>
  <div class="floor">
  [<a href="{{.Edit}}">EDIT</a>] &nbsp;

  {{ template "TAIL" $ }}
  `
EDIT = `
  {{ template "HEAD" $ }}
  <form method="POST" action="{{.Submit}}">
    <b>Title:</b> <input name=EditTitle size=80 value="{{.EditTitle}}">
    <p>
    <textarea name=Text wrap=virtual rows=30 cols=80 style="width: 95%; height: 80%"
      >{{.Text}}</textarea>
    <p>
    <input type=submit value=Save> &nbsp;
    <input type=reset>
    <tt>&nbsp; <big>[<a href={{.Cancel}}>Cancel</a>]</big></tt>
  </form>
  {{ template "TAIL" $ }}
  `
ATTACH = `
  {{ template "HEAD" $ }}
  <form method="POST" action="{{.Subject}}" enctype="multipart/form-data">
    <p>
    Upload a new attachment:
    <input type="file" name="file">
    <p>
    <input type=submit value=Save> &nbsp;
    <input type=reset>
    <tt>&nbsp; <big>[<a href={{.Cancel}}>Cancel</a>]</big></tt>
  </form>
  {{ template "TAIL" $ }}
  `

pass
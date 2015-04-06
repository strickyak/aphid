from go import bufio, bytes, fmt, reflect, regexp, sort, time
from go import html/template, net/http, io/ioutil
from go import path as P
from . import A, atemplate, bundle, util
from . import basic, flag
from lib import data

F = fmt.Sprintf

def J(*vec):
  return P.Clean(P.Join(*vec))

class Master:
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

    .t.New('HEAD').Parse(HEAD)
    .t.New('TAIL').Parse(TAIL)
    .t.New('DIR').Parse(DIR)
    .t.New('TEXT').Parse(TEXT)
    .t.New('EDIT').Parse(EDIT)
    .t.New('ATTACH').Parse(ATTACH)

  def Handle2(w, r):
    host, extra, path, root = util.HostExtraPathRoot(r)
    say host, extra, path, root
    try:
      return .Handle5(w, r, host, path, root)
    except as ex:
      say 'EXCEPTION IN Handle5', ex
      raise ex

  def Handle5(w, r, host, path, root):
    if path == '/favicon.ico':
      return

    r.ParseForm()
    query = {}
    for k, v in r.Form.items():
      say k, v
      if len(v):
        query[k] = v[0]
        say "FORM", k, v[0]

    cmd = query.get('c')

    switch cmd:
        case 'edit':
          text = query.get('Text')
          if text:
            # This is a submission.
            say 'bundle.WriteFile', path, text
            bundle.WriteFile(.bund, path, text, pw=None)
            http.Redirect(w, r, "%s%s" % (root, path), http.StatusMovedPermanently)
          
          else:
            text = bundle.ReadFile(.bund, path, pw=None)
            d = dict(Title='VIEW TEXT: %q' % path,
                     Submit='%s%s' % (root, path),
                     Filepath=path,
                     Text=text,
                     EditTitle='Bogus Title for %q' % path
                     )
            util.NativeExecuteTemplate(.t, w, 'EDIT', d)

        default:
          isDir, mTime, fSize = .bund.Stat3(path, pw=None)
          if isDir:
            dirs = .bund.ListDirs(path, pw=None)
            files = .bund.ListFiles(path, pw=None)
            dd = dict([(d, J('%s%s' % (root, path), d)) for d in dirs if d])
            ff = dict([(f, J('%s%s' % (root, path), f)) for f in files if f])
            up = J(root, path, '..') if path != '/' else ''
            d = dict(Title=path, dd=dd, ff=ff, up=up)
            say d
            util.NativeExecuteTemplate(.t, w, 'DIR', d)
          else:
            text = bundle.ReadFile(.bund, path, None)
            d = dict(Title=path,
                     Edit='%s%s?c=edit' % (root, path),
                     Filepath=path,
                     Text=text,
                     )
            util.NativeExecuteTemplate(.t, w, 'TEXT', d)

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
      <td align=right> <h2><tt>Wedit</tt></h2>
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
    <hr>
        {{ printf "%#v" $ }}
    </tt>

  </body></html>
  `
DIR = `
  {{ template "HEAD" $ }}
  <h3>Directories</h3>
  <tt><ul>
  {{ if $.up }}
    <li> <a href="{{ $.up }}">[up]</a>
  {{ end }}
  {{ range $.dd | keys }}
    <li> <a href="{{ index $.dd . }}">{{ . }}</a>
  {{ end }}
  </ul></tt>

  <h3>Files</h3>
  <tt><ul>
  {{ range $.ff | keys }}
    <li> <a href="{{ index $.ff . }}">{{ . }}</a>
  {{ end }}
  </ul></tt>

  {{ template "TAIL" $ }}
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
    <input type=hidden name="c" value="edit"> &nbsp;
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

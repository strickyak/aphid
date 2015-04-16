from go import bufio, bytes, fmt, log, reflect, regexp, sort, time
from go import html/template, net/http, io/ioutil
from go import path as P
from . import A, atemplate, bundle, markdown, util
from . import adapt, basic, flag
from lib import data

F = fmt.Sprintf
Nav = util.Nav
TIME_FORMAT = '2006-01-02T15:04:05-07:00'

#J = P.Join
def J(*vec):
  return P.Clean(P.Join(*vec))

MatchStatic = regexp.MustCompile('^/+(css|js|img|media)/(.*)$').FindStringSubmatch
MatchContent = regexp.MustCompile('^/+(([-A-Za-z0-9_]+)/)?([-A-Za-z0-9_]+)/*$').FindStringSubmatch
MatchHome = regexp.MustCompile('^/+(index.html)?$').FindStringSubmatch
MatchEditor = regexp.MustCompile('^/+([*]\\w+)$').FindStringSubmatch

MatchMdDirName = regexp.MustCompile('^[a-z][-a-z0-9_]*$').FindString
MatchMdFileName = regexp.MustCompile('^[a-z][-a-z0-9_]*[.]md$').FindString

def WeightedKey(x):
  return x.Weight, x.Name

class AFugioMaster:
  def __init__(aphid, bname, bund, users=None):
    .aphid = aphid
    must bname
    .bname = bname
    must bund
    .bund = bund
    .users = users
    .editor = Editor(master=self, bname=bname, bund=bund, users=users)
    .ReloadTemplates()
    .ReloadPageMeta()

  def MakePage(pname, modTime, fileSize):
    say pname
    slug = P.Base(pname)
    section = P.Dir(pname)
    section = '' if section == '.' else section

    fname = J('/fugio/content', '%s.md' % pname)
    md = bundle.ReadFile(.bund, fname, None)
    meta, html = markdown.ProcessWithFrontMatter(md)
    title = meta.get('title', pname) if meta else pname
    ts = meta.get('date') if meta else None
    ts = ts if ts else time.Unix(modTime, 0).Format(TIME_FORMAT)
    p = go_new(Page) {
        Title: title,
        Content: html,
        Permalink: pname,  # TODO -- host, extra
        Params: util.NativeMap(meta),
        Date: time.Parse(TIME_FORMAT, ts),
        Section: section,
        Slug: slug,
        Identifier: pname,
    }
    return p

  def WalkMdTreeMakingPages(dirname):
    say dirname
    for name, isDir, mtime, sz in sorted(.bund.List4(J('/fugio/content', dirname), pw=None)):
      if isDir and MatchMdDirName(name):
        for pair in .WalkMdTreeMakingPages(J(dirname, name)):
          say pair
          yield pair
      else:
        if sz > 0 and MatchMdFileName(name):
          pname = J(dirname, name[:-3])
          p = .MakePage(pname, mtime, sz)
          say pname, p
          yield pname, p

  def ReloadPageMeta():
    paged = dict(.WalkMdTreeMakingPages('/'))
    print paged
    page_list = paged.values()
    print page_list

    # Sort pages.
    pages_by = go_new(PagesBy) {
      ByTitle: util.NativeSlice(sorted(page_list, key=lambda x: x.Title)),
      ByDate: util.NativeSlice(sorted(page_list, reverse=True, key=lambda x: x.Date)),
      ByURL: util.NativeSlice(sorted(page_list, key=lambda x: x.Permalink)),
    }

    # Visit pages, to build tags & menus.
    menud = {}
    tags = {}
    for pname, p in paged.items():
      if p.Params:
        # Collect tags.
        taglist = p.Params.get('tags', [])
        for t in taglist:
          d = Nav(tags, t)
          d[pname] = True

        # Collect menus.
        j_menus = p.Params.get('menu')
        for which_menu in j_menus:
          j_menu = j_menus[which_menu]

          # Fetch or create the menu from menus.
          menu = Nav(menud, which_menu)

          # Make new entry, and add to that menu.
          entry = go_new(MenuEntry) {
              Identifier: pname,
              Menu: which_menu,
              Name: j_menu.get('name', pname),
              URL: '%s' % pname,
              Weight: j_menu.get('weight', 0),
              Pre: '', Post: '',
              }
          entry.DebugName = entry.Name + "/" + WeightedKey(entry)
          menu[pname] = entry

    # Sort the menus.
    for which_menu, menu in menud.items():
      say menu
      menu2 = sorted(menu.values(), key=WeightedKey)
      say 'sorted', menu2
      menud[which_menu] = util.NativeSlice(menu2)

    # Construct the site.
    .paged = paged
    .site = go_new(Site) {
      Menus: util.NativeMap(menud),
      Pages: pages_by,
      Sections: util.NativeMap(menud),
      Title: '(site-title)',
    }
    for pname, p in paged.items():
      p.Site = .site

  def ReloadTemplates():
    tpl = template.New('ROOT')
    tpl.Funcs(util.TemplateFuncs())

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
          tpl.New(name).Parse(guts)
    .tpl = tpl

  def Handle2(w, r):
    host, extra, path, root = util.HostExtraPathRoot(r)
    say host, extra, path, root
    try:
      return .Handle5(w, r, host, path, root)
    except as ex:
      say ex
      raise ex

  def Handle5(w, r, host, path, root):
    if path == '/favicon.ico':
      return

    # Special Commands.
    m = MatchEditor(path)
    if m:
      _, cmd = m
      switch cmd:
        case '*debug':
          w.Header().Set('Content-Type', 'text/plain')
          fmt.Fprintf(w, '## Front Matter ##\n')
          for k, v in .metas.items():
            fmt.Fprintf(w, '%s: %s\n', k, str(v))
          fmt.Fprintf(w, '\n## Templates ##\n')
          for t in .tpl.Templates():
            fmt.Fprintf(w, '  %#v\n', t)
        default:
          .editor.Handle5(w, r, host=host, path=path, root=root)
      return

    m = MatchStatic(path)
    if m:
      _, flavor, path = m
      say 'MatchStatic', flavor, path
      rs, nanos, size = .bund.NewReadSeekerTimeSize('/fugio/static/%s/%s' % (flavor, path))
      http.ServeContent(w, r, r.URL.Path, time.Unix(0, nanos), rs)
      return

    # If not static, it must be a page.
    m = MatchContent(path)
    if MatchHome(path):
      m = '/home', (), '', 'home'
    if m:
      _, _, section, base = m
      pname = J('/', section, base)
      p = .paged.get(pname)
      say 'MatchContent', path, section, base, pname, p
      #say sorted(.paged)
      #say .paged
      assert p, (path, section, base, pname, sorted(.paged))
      w.Header().Set('Content-Type', 'text/html')

      .tpl.ExecuteTemplate(w, 'theme/_default/single.html', p)
      return

    raise "fugio: Bad URL: %q %q" % (host, path)

pass

native: `
type MenuEntry struct {
        URL        string
        Name       string
        DebugName  string
        Menu       string
        Identifier string
        Pre        i_template.HTML
        Post       i_template.HTML
        Weight     int
        Parent     string
        // Children   Menu
}

type Page struct {
        Params          i_util.NativeMap
        Content         i_template.HTML
        Aliases         i_util.NativeSlice // []string
        // Summary         i_template.HTML
        // Status          string
        // Images          []Image
        // Videos          []Video
        // TableOfContents i_template.HTML
        // Truncated       bool
        // Draft           bool
        // PublishDate     i_time.Time
        // Tmpl            tpl.Template
        // Markup          string

        Type            string
        Title           string
        Permalink       string
        Date            i_time.Time
        Site            *Site
        Section         string
        Slug            string
        Identifier      string
}

type PagesBy struct {
        ByTitle         i_util.NativeSlice
        ByDate          i_util.NativeSlice
        ByURL           i_util.NativeSlice
}

type Site struct {
        Title          string
        Pages          *PagesBy
        // Files          []*source.File
        // Tmpl           tpl.Template
        // Taxonomies     TaxonomyList
        // Source         source.Input
        Sections       i_util.NativeMap
        // Info           SiteInfo
        // Shortcodes     map[string]ShortcodeFunc
        Menus          i_util.NativeMap
        // timer          *nitro.B
        // Targets        targetList
        // targetListInit sync.Once
        // Completed      chan bool
        // RunMode        runmode
        // params         map[string]interface{}
        // draftCount     int
        // futureCount    int
        Data           i_util.NativeMap
        Params           i_util.NativeMap
}
`

##############################################


#from go import bufio, bytes, fmt, reflect, regexp, sort, time
#from go import html/template, net/http, io/ioutil
#from go import path as P
#from . import A, atemplate, bundle
#from . import adapt, basic, flag, util
#from lib import data

class Editor:
  def __init__(master, bname, bund, users=None):
    .master = master
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
    .t.New('SITE').Parse(SITE)
    .t.New('TEXT').Parse(TEXT)
    .t.New('EDIT').Parse(EDIT)
    .t.New('EDIT_CONFIG').Parse(EDIT_CONFIG)
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

    cmd = P.Base(path)
    query = util.ParseQuery(r)
    fname = query.get('f')

    switch cmd:
        case '*':
          .t.ExecuteTemplate(w, 'SITE', .master.site)

        case '*edit_submit':
          text = query['Text']
          say 'bundle.WriteFile', fname, text
          bundle.WriteFile(.bund, fname, text, pw=None)
          http.Redirect(w, r, "%s*view?f=%s" % (root, fname), http.StatusMovedPermanently)

        case '*edit':
            text = bundle.ReadFile(.bund, fname, pw=None)
            d = dict(Title='VIEW TEXT: %q' % fname,
                     Submit='%s*edit_submit?f=%s' % (root, fname),
                     Filepath=fname,
                     Text=text,
                     EditTitle='Bogus Title for %q' % fname
                     )
            .t.ExecuteTemplate(w, 'EDIT', util.NativeMap(d))

        case '*edit_config_submit':
          x = dict(
              Title= query['EditTitle'],
              )
          s = markdown.EncodeToml(x)
          fname = '/fugio/config.toml'
          say 'bundle.WriteFile', fname, s
          bundle.WriteFile(.bund, fname, s, pw=None)
          http.Redirect(w, r, "%s*view?f=%s" % (root, fname), http.StatusMovedPermanently)

        case '*edit_config':
          s = bundle.ReadFile(.bund, fname, pw=None)
          x = markdown.EvalToml(s)
          fname = '/fugio/config.toml'
          d = dict(Title='Edit Site Configuration',
                   Submit='%s*edit_submit' % root,
                   Text=text,
                   EditTitle=x.get('Title')
                   )
          .t.ExecuteTemplate(w, 'EDIT', util.NativeMap(d))

        case '*view':
          isDir, modTime, fSize = .bund.Stat3(fname, pw=None)
          if isDir:
            dirs = .bund.ListDirs(fname, pw=None)
            files = .bund.ListFiles(fname, pw=None)

            dd = dict([(d, J(fname, d)) for d in dirs if d])
            ff = dict([(f, J(fname, f)) for f in files if f])
            up = '/' if fname == '/' else J(fname, '..')
            d = dict(Title=fname, root=root, dd=dd, ff=ff, up=up)

            say d
            .t.ExecuteTemplate(w, 'DIR', util.NativeMap(d))
          elif fSize:
            br = .bund.MakeReader(fname, pw=None, raw=False, rev=None)
            http.ServeContent(w, r, fname, adapt.UnixToTime(modTime), br)
          else:
            raise 'Cannot view empty or deleted file: %q' % fname

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
    <li> <a href="{{$.root}}*view?f={{ $.up }}">[up]</a>
  {{ end }}
  {{ range $.dd | keys }}
    <li> <a href="{{$.root}}*view?f={{ index $.dd . }}">{{ . }}</a>
  {{ end }}
  </ul></tt>

  <h3>Files</h3>
  <tt><ul>
  {{ range $.ff | keys }}
    <li> <a href="{{$.root}}*view?f={{ index $.ff . }}">{{ . }}</a>
         &nbsp; &nbsp;
         [<a href="{{$.root}}*edit?f={{ index $.ff . }}">edit</a>]
  {{ end }}
  </ul></tt>

  {{ template "TAIL" $ }}
  `
SITE = `
  {{ template "HEAD" $ }}

  This is for the site:
  <p>
  <tt>{{ printf "%#v" $ }}</tt>
  <p>
  [<a href="TODO">TODO</a>] &nbsp;
  <p>

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
EDIT_CONFIG = `
  {{ template "HEAD" $ }}
  <form method="POST" action="{{.Submit}}">
    <b>Site Title:</b>
    <input name=EditTitle size=80 value="{{.EditTitle}}">
    <br>
    <input type=hidden name="c" value="edit">
    <input type=submit value=Save> &nbsp; &nbsp;
    <input type=reset> &nbsp; &nbsp;
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

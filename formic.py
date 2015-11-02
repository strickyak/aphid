from go import bufio, bytes, fmt, log, reflect, regexp, sort, sync, time
from go import html/template, net/http, io, io/ioutil
from go import path as P
from . import A, atemplate, bundle, keyring, markdown, pubsub, util
from . import adapt, basic, conv, flag
from lib import data

F = fmt.Sprintf
Nav = util.Nav
HUGO_TIME_FORMAT = '2006-01-02T15:04:05-07:00'

def J(*vec):
  return P.Clean(P.Join(*vec))

MatchContent = regexp.MustCompile('^/+(([-A-Za-z0-9_]+)/)?([-A-Za-z0-9_]+)/*$').FindStringSubmatch
MatchHome = regexp.MustCompile('^/+(@[^/]*/+)?(index[.]html)?$').FindStringSubmatch
MatchCurator = regexp.MustCompile('^/+([*]+\\w*)').FindStringSubmatch
MatchTaxonomy = regexp.MustCompile('^/+(tags)(?:/(\\w*)/?)?').FindStringSubmatch

MatchMdDirName = regexp.MustCompile('^[a-z][-a-z0-9_]*$').FindString
MatchMdFileName = regexp.MustCompile('^[a-z][-a-z0-9_]*[.]md$').FindString
MatchMdEditName = regexp.MustCompile('^([a-z][-a-z0-9_]*/)?([a-z][-a-z0-9_]*)$').FindStringSubmatch
MatchMediaDirName = regexp.MustCompile('^[-A-Za-z0-9_{}]+$').FindString
MatchMediaFileName = regexp.MustCompile('^[-A-Za-z0-9_.{}]+$').FindString

# For uploading attachments
DOTFILE = regexp.MustCompile('(^[.]|[/][.])').FindString
MATCH_FILENAME = regexp.MustCompile('.*filename="([^"]+)"').FindStringSubmatch
MatchHrefOrSrc = regexp.MustCompile(" (href|src)=\"/.")

def WeightedKey(x):
  return x.Weight, x.Name

class FormicMaster:
  def __init__(aphid, bname, bund, config):
    .mu = go_new(sync.Mutex)
    .aphid = aphid
    .bus = aphid.bus
    must bname
    .bname = bname
    must bund
    .bund = bund
    .curator = Curator(master=self, bname=bname, bund=bund, config=config)

    sub = pubsub.Sub(key1='WriteFile', re2=None, fn=.ReloadBecauseOfThing)
    .bus.Subscribe(sub)

    .Reload()

  def ReloadBecauseOfThing(thing):
    # TODO: use a channel for driving reload.
    say thing
    .Reload()

  def Reload():
    .mu.Lock()
    with defer .mu.Unlock():
      .ReloadTemplates()
      .ReloadPageMeta()

  def MakePage(pname, modTime, fileSize):
    say pname
    slug = P.Base(pname)
    section = P.Dir(pname)
    section = '' if section == '.' else section

    fname = J('/formic/content', '%s.md' % pname)
    md = bundle.ReadFile(.bund, fname, None)
    meta, _, html = markdown.ProcessWithFrontMatter(md)
    title = meta.get('title', pname) if meta else pname
    ts = meta.get('date') if meta else None
    ts = ts if ts else modTime.Format(HUGO_TIME_FORMAT)
    ptype = meta.get('type', '') if meta else ''
    p = go_new(Page) {
        Title: title,
        Content: html,
        Type: ptype,
        Permalink: pname,  # TODO -- host, extra
        Params: util.NativeMap(meta),
        Date: time.Parse(HUGO_TIME_FORMAT, ts),
        Section: section,
        Slug: slug,
        Identifier: pname,
    }
    p.Age = (time.Now().Unix() - p.Date.Unix()) / 86400.0
    say p.Age, time.Now().Unix(), p.Date.Unix(), p.Date
    return p

  def WalkMdTreeMakingPages(dirname):
    say dirname
    for name, isDir, modTime, sz in sorted(.bund.List4(J('/formic/content', dirname), pw=None)):
      if modTime > 9999999999:
        modTime = modTime // 1000
      if isDir and MatchMdDirName(name):
        for pair in .WalkMdTreeMakingPages(J(dirname, name)):
          say pair
          yield pair
      else:
        if sz > 0 and MatchMdFileName(name):
          pname = J(dirname, name[:-3]).strip('/')
          p = .MakePage(pname, time.Unix(0, modTime*1000000000), sz)
          yield pname, p

  def WalkMediaTree(dirname):
    say dirname
    for name, isDir, modTime, sz in sorted(.bund.List4(J('/formic/static/media', dirname), pw=None)):
      if modTime > 9999999999:
        modTime = modTime // 1000
      say name, isDir, modTime, sz
      # Actually we don't upload into subdirs yet.
      if isDir and MatchMediaDirName(name):
        for pair in .WalkMediaTree(J(dirname, name)):
          say pair
          yield pair
      else:
        if sz > 0 and MatchMediaFileName(name):
          pname = J(dirname, name).strip('/')
          p = go_new(MediaFile) {
              Date: time.Unix(0, modTime*1000000000),
              Size: sz,
              Identifier: pname,
              Slug: name,
              Directory: dirname,
              }
          p.Age = (time.Now().Unix() - p.Date.Unix()) / 86400.0
          say pname, p.Age, time.Now().Unix(), p.Date.Unix(), p.Date, modTime
          yield pname, p

  def ReloadPageMeta():
    page_d = dict(.WalkMdTreeMakingPages('/'))
    print page_d
    media_d = dict(.WalkMediaTree('/'))
    print media_d
    page_list = page_d.values()
    print page_list
    media_list = media_d.values()
    print media_list

    # Sort pages.
    pages_by = go_new(PagesBy) {
      ByTitle: util.NativeSlice(sorted(page_list, key=lambda x: x.Title)),
      ByDate: util.NativeSlice(sorted(page_list, reverse=True, key=lambda x: x.Date.Unix())),
      ByURL: util.NativeSlice(sorted(page_list, key=lambda x: x.Permalink)),
    }
    # Sort media.
    media_by = go_new(MediaBy) {
      ByDate: util.NativeSlice(sorted(media_list, reverse=True, key=lambda x: x.Date.Unix())),
      ByURL: util.NativeSlice(sorted(media_list, key=lambda x: x.Identifier)),
    }

    # Visit pages, to build tags & menus.
    menud = {} ## which_menu -> pagename -> MenuEntry
    tags = {}  ## tagname -> pagename -> p
    for pname, p in page_d.items():
      if p.Params:
        # Collect tags.
        say '@tags', p.Params.get('tags', [])
        for t in p.Params.get('tags', []):
          say '@tags', t
          d = Nav(tags, t)
          d[pname] = p

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
              URL: '/%s' % pname,
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

    # Sort pages for tags.
    tags_pages_by = {}
    for t, pmap in tags.items():
      ## pmap :: pname -> p
      page_list = pmap.values()

      tags_pages_by[t] = go_new(PagesBy) {
        ByTitle: util.NativeSlice(sorted(page_list, key=lambda x: x.Title)),
        ByDate: util.NativeSlice(sorted(page_list, reverse=True, key=lambda x: x.Date.Unix())),
        ByURL: util.NativeSlice(sorted(page_list, key=lambda x: x.Permalink)),
      }
    # Construct the site.
    try:
      site_toml = bundle.ReadFile(.bund, '/formic/config.toml', pw=None)
      site_d = markdown.EvalToml(site_toml)
    except as ex:
      # TODO -- log error
      site_d = dict()

    .page_d, .pages_by = page_d, pages_by
    .media_d, .media_by = media_d, media_by
    .tags, .tags_pages_by = tags, tags_pages_by
    .site = go_new(Site) {
      Menus: util.NativeMap(menud),
      Pages: pages_by,
      Sections: util.NativeMap(menud),
      Title: site_d.get('title', '(this site needs a title)'),
      BaseURL: site_d.get('baseurl', 'http://127.0.0.1/...FixTheBaseURL.../'),
      Media: media_by,
    }
    # Pages link back up to Site
    for pname, p in page_d.items():
      p.Site = .site

  def ReloadTemplates():
    tpl = template.New('ROOT')
    tpl.Funcs(util.TemplateFuncs())

    try:
      dnames = bundle.ListDirs(.bund, '/formic/layouts')
    except:
      dnames = []
    for dname in dnames:
      try:
        tnames = bundle.ListFiles(.bund, J('/formic/layouts', dname))
      except:
        tnames = []
      for tname in tnames:
        if tname.endswith('.html'):
          name = J('theme', dname, tname)
          guts = bundle.ReadFile(.bund, J('/formic/layouts', dname, tname))
          tpl.New(name).Parse(guts)
    .tpl = tpl

  def Handle2(w, r):
    try:
      say 'Handle2'
      host, extra, path, root = util.HostExtraPathRoot(r)
      say host, extra, path, root
      return .Handle5(w, r, host, path, root)
    except as ex:
      say ex
      print >>w, '<br><br>\n\n*** ERROR *** <br><br>\n\n*** %s ***\n\n***' % ex
      raise ex
      return # raise ex

  def Handle5(w, r, host, path, root):
    say 'Handle5'
    # Special Commands.
    m = MatchCurator(path)
    if m:
      _, cmd = m
      say m, host, cmd, root
      .curator.Handle5(w, r, host=host, path=cmd, root=root)
      return

    if DOTFILE(path):
      raise 'Dotfile in path not allowed: %q' % path

    isStatic = False
    try:
      isDir, modTime, fSize = .bund.Stat3(J('/formic/static', path), pw=None)
      say isDir, modTime, fSize, path
      isStatic = fSize and not isDir
    except:
      pass

    if isStatic:
      rs, nanos, size = .bund.NewReadSeekerTimeSize(J('/formic/static', path))
      http.ServeContent(w, r, r.URL.Path, time.Unix(0, nanos), rs)
      return

    # We hardwire the taxonomy "tags".
    m = MatchTaxonomy(path)
    if m:
      _, tax, value = m
      assert tax == 'tags', tax
      if value:
        raise 'TODO value %q' % value
        by = .tags_pages_by.get('value')
        if by:
          d = util.NativeMap(dict(
            Data=util.NativeMap(dict(
              Pages=by,
              )),
            Title='Pages with tag %q' % value,
            ))
          .tpl.ExecuteTemplate(w, J('theme', '_default', 'list.html'), d)
        else:
          print >>w, 'There are no pages with tag %q.' % value
      else:
        # Generate list.
        print >>w, '<ul>'
        for tag in .tags:
          print >>w, '<li><a href="%stags/%s">%s</a>' % (root, tag, tag)
        print >>w, '</ul>'
      return




    # If it is not a curator command and not a static file and not a Taxonomy, it must be a page.
    m = MatchContent(path)
    if MatchHome(path):
      say 'MatchHome'
      m = '/home', (), '', 'home'
      # TODO -- try to serve .../formic/layouts/index.html for HOME
    if m:
      _, _, section, base = m
      pname = J(section, base).strip('/')
      p = .page_d.get(pname)
      say 'MatchContent', path, section, base, pname, p

      w.Header().Set('Content-Type', 'text/html; charset=UTF-8')
      if not p:
        # Page does not exist.
        w.WriteHeader(404)
        print >>w, '404 PAGE NOT FOUND.\n\n'
        print >>w, 'pname = %q' % pname
        return

      ptype = p.Type if p.Type else '_default'
      p.Root = root  # TODO -- fix critical race when concurrent.
      .tpl.ExecuteTemplate(w, J('theme', ptype, 'single.html'), p)
      return

    raise "formic: Bad URL: %q %q" % (host, path)

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
        Root      string
}

type MediaFile struct {
        Date            i_time.Time
        Size            int64
        Identifier      string
        Slug            string
        Directory       string
        Age             float64
        Root      string
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
        Age             float64
        Site            *Site
        Section         string
        Slug            string
        Identifier      string

        Root      string
}

type PagesBy struct {
        ByTitle         i_util.NativeSlice
        ByDate          i_util.NativeSlice
        ByURL           i_util.NativeSlice
}

type MediaBy struct {
        ByTitle         i_util.NativeSlice
        ByDate          i_util.NativeSlice
        ByURL           i_util.NativeSlice
}

type Site struct {
        Title          string
        BaseURL        string
        Pages          *PagesBy
        Media          *MediaBy
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

        Root      string
}
`

##############################################

class Curator:
  def __init__(master, bname, bund, config):
    .master = master
    .bname = bname
    must bund
    .bund = bund
    .config = config
    .pwName = config['pw']
    .wantHash = keyring.Ring[.pwName].doubleMD5
    .ReloadTemplates()

  def ReloadTemplates():
    .t = template.New('Curator')
    .t.Funcs(util.TemplateFuncs())
    .t.Parse(CURATOR_TEMPLATES)

  def Handle5(w, r, host, path, root):
    user_pw = basic.GetBasicPw(w, r, root)
    if user_pw:
      user, pw = user_pw
    else:
      return  # We demanded Basic Authorization.
    say user, host, path, root

    # Hash the given password into hex.
    hashed2 = conv.DoubleMD5(pw)

    if hashed2 != .wantHash or not len(user):
      w.Header().Set("WWW-Authenticate", 'Basic realm="%s"' % root)
      w.WriteHeader(401)
      print >>w, 'Wrong User or Password -- Hit RELOAD and try again.'
      return

    say path
    cmd = P.Base(path)
    say cmd
    query = util.ParseQuery(r)
    fname = query.get('f', '/')

    switch cmd:
      case '*':
        cmd = '*curate'
      case '**':
        cmd = '**view'
    switch cmd:
        case '*curate':
          d = dict(
              Site=.master.site,
              Root=root,
              )
          say d
          .t.ExecuteTemplate(w, 'CURATE', util.NativeMap(d))

        case '**site':
          d = dict(
              Site=.master.site,
              Root=root,
              )
          .t.ExecuteTemplate(w, 'SITE', util.NativeMap(d))

        case '**edit_site_submit':
          if query['submit'] == 'Save':
            d = dict(
              title= query['title'],
              baseurl= query['baseurl'],
              Root=root,
              )
            toml = markdown.EncodeToml(util.NativeMap(d))
            bundle.WriteFile(.bund, '/formic/config.toml', toml, pw=None)
            .master.Reload()
          http.Redirect(w, r, "%s**site" % root, http.StatusTemporaryRedirect)

        case '**edit_site':
          d = dict(
            Site=.master.site,
            Root=root,
            )
          .t.ExecuteTemplate(w, 'EDIT_SITE', util.NativeMap(d))

        case '**delete_file_submit':
          delfile = query['delfile']
          if query.get('DeleteFile'):
            bundle.WriteFile(.bund, delfile, '', pw=None)
          say P.Dir(delfile)
          http.Redirect(w, r, '%s**view?f=%s' % (root, P.Dir(delfile)), http.StatusTemporaryRedirect)

        case '**delete_file':
          d = dict(
            Title='Upload Media Attachment',
            Action='%s**delete_file_submit' % root,
            fname=fname,
            Root=root,
            )
          .t.ExecuteTemplate(w, 'DELETE', util.NativeMap(d))

        case '*attach_media_submit':
          say query

          r.ParseMultipartForm(1024*1024)
          say r.MultipartForm.File['file'][0].Header
          cd = r.MultipartForm.File['file'][0].Header.Get('Content-Disposition')
          say cd
          match = MATCH_FILENAME(cd)
          say match
          f = match[1] if match else ''
          if f:
            fname = r.MultipartForm.File['file'][0].Filename
            editdir = r.MultipartForm.Value['EditDir'][0]
            fpath = J(editdir, conv.EncodeCurlyStrong(fname))
            say editdir, fname, fpath

            fd = r.MultipartForm.File['file'][0].Open()
            br = bufio.NewReader(fd)
            cr = bundle.ChunkReaderAdapter(br)
            cw = .bund.MakeWriter(fpath, pw=None, mtime=0, raw=None)
            bundle.CopyChunks(cw, cr)
            cw.Close()
            fd.Close()
            .master.Reload()

            if editdir == 'formic/static/media':
              http.Redirect(w, r, '%s*' % root, http.StatusTemporaryRedirect)
            else:
              http.Redirect(w, r, '%s**view?f=%s' % (root, editdir), http.StatusTemporaryRedirect)
          else:
            print >>w, 'No file was uploaded.  Go back and try again.'

        case '*attach_media':
          d = dict(Title='Upload Media Attachment',
                   Action='%s*attach_media_submit' % root,
                   EditDir='formic/static/media',
                   EditDirFixed='1',
                   Root=root,
                   )
          .t.ExecuteTemplate(w, 'ATTACH', util.NativeMap(d))

        case '**attach_file':
          d = dict(Title='Upload Media Attachment',
                   Action='%s*attach_media_submit' % root,
                   EditDir='%s' % query.get('dir', '/formic/static/media'),
                   EditDirFixed='',
                   Root=root,
                   )
          .t.ExecuteTemplate(w, 'ATTACH', util.NativeMap(d))

        case '*edit_page_submit':
          say query
          if query.get('submit') != 'Save':
            # Cancel; don't save.
            http.Redirect(w, r, "%s%s" % (root, fname), http.StatusTemporaryRedirect)
            return

          edit_path = query.get('EditPath', '')
          say edit_path
          edit_path = edit_path.strip().lower() if edit_path else ''
          say edit_path
          if edit_path:
            m = MatchMdEditName(edit_path)
            if not m:
              raise 'Bad file path: %q' % edit_path

            _, section, slug = m
            fname = J(section, slug).strip('/')

          if not fname:
            raise 'Error: No fname given'

          edit_md = query['EditMd']
          say query.get('DeletePage')
          if query.get('DeletePage'):
            # "Delete" the file, but writing empty file.
            text = ''
          else:
            edit_title = query['EditTitle'].strip()
            main_name = query['EditMainName'].strip()
            main_weight = 0
            try:
              main_weight = int(query['EditMainWeight'].strip())
            except:
              pass
            if main_name:
              edit_menu = util.NativeMap(dict(main=util.NativeMap(dict(
                  name=main_name,
                  weigth=main_weight,
                  ))))
            else:
              edit_menu = util.NativeMap(dict())

            edit_type = query['EditType'].strip()

            edit_aliases = util.NativeSlice(
                [s.strip() for s in query['EditAliases'].strip().split(',')]
                )
            toml = markdown.EncodeToml(util.NativeMap(dict(
                title=edit_title,
                aliases=edit_aliases,
                type=edit_type,
                menu=edit_menu,
                )))
            text = '+++\n' + toml + '\n+++\n' + edit_md

            say 'bundle.WriteFile', fname, edit_title, edit_md, toml, text
          bundle.WriteFile(.bund, J('/formic/content', fname + '.md'), text, pw=None)
          .master.Reload()
          if text:
            http.Redirect(w, r, "%s%s" % (root, fname), http.StatusTemporaryRedirect)
          else:
            http.Redirect(w, r, "%s*" % root, http.StatusTemporaryRedirect)
          return

        case '*new_page':
          d = dict(Title='Create New Page',
                   Submit='%s*edit_page_submit' % root,
                   Filepath='',
                   EditMd='[Enter the page content here.]',
                   EditTitle='Untitled',
                   EditAliases='',
                   EditType='',
                   EditMainName='',
                   EditMainWeight=0,
                   DebugMeta='',
                   new_page='1',  # True
                   Root=root,
                   )
          .t.ExecuteTemplate(w, 'EDIT_PAGE', util.NativeMap(d))

        case '*edit_page':
          pname = fname
          filename = J('/formic/content', fname + '.md')

          text = bundle.ReadFile(.bund, filename, pw=None)
          meta, md, html = markdown.ProcessWithFrontMatter(text)

          main_d = meta.get('menu', {}).get('main')
          EditMainName = main_d.get('name', '') if main_d else ''
          EditMainWeight = main_d.get('weight', 0) if main_d else 0

          d = dict(Title='Edit Page %q' % fname,
                   Submit='%s*edit_page_submit?f=%s' % (root, fname),
                   Filepath=fname,
                   EditMd=md,
                   EditTitle=meta.get('title', 'Untitled'),
                   EditType=meta.get('type', ''),
                   EditAliases=','.join(meta.get('aliases', [])),
                   EditMainName=EditMainName,
                   EditMainWeight=EditMainWeight,
                   DebugMeta=meta,
                   new_page='',  # Empty for False
                   Root=root,
                   )
          .t.ExecuteTemplate(w, 'EDIT_PAGE', util.NativeMap(d))

        case '**edit_text_submit':
          if query['submit'] == 'Save':
            text = query['EditText']
            say 'bundle.WriteFile', fname, text
            bundle.WriteFile(.bund, fname, text, pw=None)
            .master.Reload()
          http.Redirect(w, r, "%s**view?f=%s" % (root, P.Dir(fname)), http.StatusTemporaryRedirect)

        case '**edit_text':
          edittext = bundle.ReadFile(.bund, fname, pw=None)
          d = dict(Title='VIEW TEXT: %q' % fname,
                   Submit='%s**edit_text_submit?f=%s' % (root, fname),
                   Filepath=fname,
                   EditText=edittext,
                   Root=root,
                   )
          .t.ExecuteTemplate(w, 'EDIT_TEXT', util.NativeMap(d))

        case '**view':
          isDir, modTime, fSize = .bund.Stat3(fname, pw=None)
          if isDir:
            dirs = .bund.ListDirs(fname, pw=None)
            files = .bund.ListFiles(fname, pw=None)

            dd = dict([(d, J(fname, d)) for d in dirs if d])
            ff = dict([(f, J(fname, f)) for f in files if f])
            up = '/' if fname == '/' else J(fname, '..')
            d = dict(Title=fname, dir=fname, dd=dd, ff=ff, up=up,
                     Root=root,
                     )

            say d
            .t.ExecuteTemplate(w, 'DIR', util.NativeMap(d))
          elif fSize:
            ct = query.get('ct')
            if ct:
              w.Header().Set('Content-Type', ct)
            br, _ = .bund.MakeReaderAndRev(fname, pw=None, raw=False, rev=None)
            http.ServeContent(w, r, fname, adapt.UnixToTime(modTime), br)
          else:
            raise 'Cannot view empty or deleted or nonexistant file: %q' % fname
        default:
          raise 'Unknown command: %q' % cmd
    return

CURATOR_TEMPLATES = `
{{define "HEAD"}}
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
            .form {
              background-color: yellow;
              padding: 30px;
            }
          </style>
        </head><body><tt>
          <table class="title-table" width=100% cellpadding=10><tr>
            <td align=center> <h2 class="title"><ttx>{{.Title}}</ttx></h2>
            <td align=right> <h2><ttx>*Curator*</ttx></h2>
          </tr></table>
          <div class="stuff">
{{end}}
{{define "TAIL"}}
          </div>

          <br> <br> <br> <br>
          <hr>
          <ttx>
            <dl><dt>DEBUG:</dt>
            <dd><dl>
            {{ range (keys $) }}
              <dt> <b>{{ printf "%s:" . }}</b>
              <dd> {{ printf "%#v" (index $ .) }}
            {{ end }}
            </dl></dd></dl>
          </ttx>

        </tt></body></html>
{{end}}
{{define "DIR"}}
        {{ template "HEAD" $ }}

        <h3>Directories</h3>
        <ul>
        {{ if $.up }}
          <li> <a href="{{$.Root}}**view?f={{ $.up }}">[up]</a>
        {{ end }}
        {{ range $.dd | keys }}
          <li> <a href="{{$.Root}}**view?f={{ index $.dd . }}">{{ . }}</a>
        {{ end }}
        </ul>

        <h3>Files</h3>
        [<a href="{{$.Root}}**attach_file?dir={{.dir}}">Upload File</a>]
        <ul>
        {{ range $.ff | keys }}
          <li> <a href="{{$.Root}}**view?f={{ index $.ff . }}">{{ . }}</a>
               &nbsp; &nbsp;
               [<a href="{{$.Root}}**view?f={{ index $.ff . }}&ct=text/plain">text/plain</a>]
               &nbsp; &nbsp;
               [<a href="{{$.Root}}**edit_text?f={{ index $.ff . }}">edit</a>]
               &nbsp; &nbsp;
               [<a href="{{$.Root}}**delete_file?f={{ index $.ff . }}">delete</a>]
        {{ end }}
        </ul>

        {{ template "TAIL" $ }}
{{end}}
{{define "SITE"}}
        {{ template "HEAD" $ }}
        <ttx><ul>
          <li>Site Title = "{{.Site.Title}}"
          <li>Base URL = "{{.Site.BaseURL}}"
          <li>[<a href="{{$.Root}}**edit_site">Edit Site</a>]
        </ul></ttx>

        {{ template "TAIL" $ }}
{{end}}
{{define "EDIT_SITE"}}
        {{ template "HEAD" $ }}

        <table border=1><tr><td>
        <form method="POST" action="/**edit_site_submit">
          <br><br>
          Site Title: <input type=text size=60 name=title value={{.Site.Title}}>
          <br><br>
          Base URL: <input type=text size=60 name=baseurl value={{.Site.BaseURL}}>
          <br><br>
          <input type=submit name=submit value=Save> &nbsp; &nbsp;
          <input type=reset> &nbsp; &nbsp;
          <input type=submit name=submit value=Cancel> &nbsp; &nbsp;
        </form>
        </table>

        {{ template "TAIL" $ }}
{{end}}
{{define "TEXT"}}
        {{ template "HEAD" $ }}
        <pre>{{.Text}}</pre>
        </div>
        <div class="floor">
        [<a href="{{$.Root}}{{.Edit}}">EDIT</a>] &nbsp;

        {{ template "TAIL" $ }}
{{end}}
{{define "EDIT_TEXT"}}
        {{ template "HEAD" $ }}
        <form method="POST" action="{{$.Root}}{{.Submit}}">
          <p>
          <textarea name=EditText wrap=virtual rows=30 cols=80 style="width: 95%; height: 70%"
            >{{.EditText}}</textarea>
          <p>
          <input type=submit name=submit value=Save> &nbsp; &nbsp;
          <input type=reset> &nbsp; &nbsp;
          <input type=submit name=submit value=Cancel> &nbsp; &nbsp;
        </form>
        {{ template "TAIL" $ }}
{{end}}

{{/***************************************************/}}

{{define "EDIT_PAGE"}}
        {{ template "HEAD" $ }}
        <form method="POST" action="{{.Submit}}">
          {{ if .new_page }}
            <b>Page Name</b> (one word, all lowercase, also digits and dash, for the URL path):
            <br>
            <input name=EditPath size=40 value="{{.EditTitle}}"> <!-- TODO: Is this right? -->
            <br> <br>
          {{ end }}

          <b>Page Title:</b>
          <input name=EditTitle size=80 value="{{.EditTitle}}">
          <br> <br>

          <b>Page body, using Markdown syntax:</b>
          <textarea name=EditMd wrap=virtual rows=30 cols=80 style="width: 95%; height: 70%"
            >{{.EditMd}}</textarea>
          <br> <br>

          <input type=submit name=submit value=Save> &nbsp; &nbsp;
          <input type=reset> &nbsp; &nbsp;
          <input type=submit name=submit value=Cancel> &nbsp; &nbsp;
          <br> <br>

          <dl><dt><b>Advanced Options:</b><dd>
            Check this box to delete the page:
            <input type="checkbox" name=DeletePage value="1">
            <br> <br>

            Name in Menu:
            <input name=EditMainName size=40 value="{{.EditMainName}}">
            &nbsp; &nbsp; Weight:
            <input name=EditMainWeight size=6 value="{{.EditMainWeight}}">
            <br> <br>

            Type of Page (leave it blank if you do not know):
            <input name=EditType size=20 value="{{.EditType}}">
            <br> <br>

            <!--
            Aliases:
            <input name=EditAliases size=80 value="{{.EditAliases}}">
            <br> <br>
            -->
            <input name=EditAliases type=hidden value="{{.EditAliases}}">

          </dd></dl>
        </form>
        {{ template "TAIL" $ }}
{{end}}

{{define "DELETE"}}
        {{ template "HEAD" $ }}
        <form method="POST" action="{{.Action}}">
          <input type=hidden name=delfile value={{.fname}}>
          <p>
          Deleting file: <b>"{{.fname}}"</b>
          <p>
          <input type="checkbox" name=DeleteFile value="1"> &nbsp; Check to Confirm.
          <br> <br>
          <input type=submit value=Delete> &nbsp; &nbsp;
        </form>
        {{ template "TAIL" $ }}
{{end}}

{{define "ATTACH"}}
        {{ template "HEAD" $ }}
        <form method="POST" action="{{.Action}}" enctype="multipart/form-data">
          <p>
          Upload a new attachment:
          <input type="file" name="file">
          <br> <br>
          {{ if .EditDirFixed }}
          <input type=hidden name=EditDir value={{.EditDir}}>
          {{ else }}
          Directory: <input type=text name=EditDir value={{.EditDir}} size=40> &nbsp; &nbsp;
          <br> <br>
          {{ end }}
          <br> <br>
          <input type=submit value=Save> &nbsp; &nbsp;
          <input type=reset> &nbsp; &nbsp;
          <big>[<a href={{.Cancel}}>Cancel</a>]</big>
        </form>
        {{ template "TAIL" $ }}
{{end}}

{{define "CURATE"}}
        {{ template "HEAD" $ }}
        <h3>Site:</h3>
        <table border=1 cellpadding=5>
          <tr><th>Site Title<th>Base URL
          <tr><td>"{{.Site.Title}}"<td>{{.Site.BaseURL}}
        </table>

        <h3>Pages:</h3>
        [<a href="{{$.Root}}*new_page">Create New Page</a>]
        <table border=1 cellpadding=4>
          <tr><th>Path &amp; Edit Link<th>Title &amp; View Link<th>Days Old<th>Date
          {{ range .Site.Pages.ByDate }}
            <tr>
              <td><a href="{{$.Root}}*edit_page?f={{.Identifier}}">{{.Identifier}}
              <td><a href="{{$.Root}}{{.Identifier}}">{{.Title}}</a>
              <td align=right>{{printf "%.0f" .Age}}
              <td>{{.Date.Format "Mon, 02-Jan-2006 15:04 MST"}}
          {{ end }}
        </table>

        <h3>Media:</h3>
        <table border=1 cellpadding=4>
          [<a href="{{$.Root}}*attach_media">Upload New Media</a>]
          <tr><th>Path<th>Size<th>Days Old<th>Date
          {{ range .Site.Media.ByDate }}
            <tr>
              <td><a href="{{$.Root}}media/{{.Identifier}}">{{.Identifier}}</a>
              <td align=right>{{.Size}}
              <td align=right>{{printf "%.0f" .Age}}
              <td>{{.Date.Format "Mon, 02-Jan-2006 15:04 MST"}}
          {{ end }}
        </table>

        {{ template "TAIL" $ }}
{{end}}
`
pass

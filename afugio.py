from go import bufio, bytes, fmt, log, reflect, regexp, sort, time
from go import html/template, net/http, io/ioutil
from go import path as P
from . import A, atemplate, bundle, markdown, util
from . import basic, flag
from lib import data

F = fmt.Sprintf
J = P.Join

MatchStatic = regexp.MustCompile('^/+(css|js|img|media)/(.*)$').FindStringSubmatch
MatchSimplePage = regexp.MustCompile('^/+([-A-Za-z0-9_]+)/*$').FindStringSubmatch
MatchHome = regexp.MustCompile('^/+(index.html)?$').FindStringSubmatch
MatchCommand = regexp.MustCompile('^/+[*](\\w+)$').FindStringSubmatch

class AFugioMaster:
  def __init__(aphid, bname, bund=None, users=None):
    .aphid = aphid
    .bname = bname
    must bund
    .bund = bund
    .users = users
    .ReloadTemplates()
    .ReloadFrontMatter()

  def ReloadFrontMatter():
    fronts = {}
    try:
      fnames = bundle.ListFiles(.bund, '/fugio/content')
    except:
      fnames = []
    for fname in fnames:
      if fname.endswith('.md'):
        try:
          guts = bundle.ReadFile(.bund, J('/fugio/content', fname))
          fname = fname[:-3]  # Strip ".md"
          front, back = markdown.Process(guts)
          fronts[fname] = front
        except as ex:
          log.Printf('ReloadFrontMatter: ERROR slurping %q: %s', fname, ex)
    .fronts = fronts

    # Visit pages, to build tags & menus.
    tags = {}
    main_menu = {}
    menus = {}
    for page, json in .fronts.items():
      if json is not None:
        # Collect tags.
        taglist = json.get('tags', [])
        for t in taglist:
          d = tags.get(t)
          if not d:
            d = {}
            tags[t] = d
          d[page] = True

        # Collect menus.
        j_menus = json.get('menu')
        for which_menu in json.get('menu'):
          j_menu = j_menus[which_menu]

          menu = menus.get(which_menu, [])
          menus[which_menu] = menu

          menu_item =dict(
              Identifier=page,
              Menu=which_menu,
              Name=j_menu.get('name', page),
              URL='/%s' % page,
              Weight=j_menu.get('weight', 0.0),
              Pre='', Post='',
              Parent='', Childern=[],
              )
          menu.append(util.NativeMap(menu_item))

    # Sort the menus.
    def WeightedKey(x):
      try:
        w = float(x.get('weight', 0))
      except:
        w = 0.0
      return (w, x.get('Identifier', "?"))

    for which_menu, menu in menus.items():
      menu.sort(key=lambda x: WeightedKey(x))
      menus[which_menu] = util.NativeSlice(menu)
    menus = util.NativeMap(menus)
    .site = util.NativeMap(dict(Menus=menus))

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
    try:
      return .Handle5(w, r, host, path, extra)
    except as ex:
      say ex
      raise ex

  def Handle5(w, r, host, path, extra):
    if path == '/favicon.ico':
      return

    m = MatchStatic(path)
    if m:
      _, flavor, path = m
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

      fname = J('/fugio/content', '%s.md' % page)
      isDir, modTime, fSize = .bund.Stat3(fname, pw=None)
      if isDir:
        raise 'Error: isDir: %q' % fname
      md = bundle.ReadFile(.bund, fname, None)
      front, html = markdown.Process(md)
      ts = front.get('date') if front else None
      ts = ts if ts else time.Unix(modTime, 0).Format(time.RFC1123)
      d = dict(
          Title=path,
          Content=html,
          Permalink=J(extra, path) if extra else path,
          Params=front,
          Date=ts,
          Site=.site,
          )
      .tpl.ExecuteTemplate(w, 'theme/_default/single.html', util.NativeMap(d))
      return

    # Special Commands.
    m = MatchCommand(path)
    if m:
      _, cmd = m
      switch cmd:
        case 'debug':
          w.Header().Set('Content-Type', 'text/plain')
          fmt.Fprintf(w, '## Front Matter ##\n')
          for k, v in .fronts.items():
            fmt.Fprintf(w, '%s: %s\n', k, str(v))
          fmt.Fprintf(w, '\n## Templates ##\n')
          for t in .tpl.Templates():
            fmt.Fprintf(w, '  %#v\n', t)
        default:
          w.Header().Set('Content-Type', 'text/plain')
          fmt.Fprintf(w, '*** Unknown Command: %q\n', path)
      return

    raise "fugio: Bad URL: %q %q" % (host, path)

pass

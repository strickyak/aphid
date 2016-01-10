from go import bufio, bytes, fmt, regexp, time
from go import html/template, net/http, io/ioutil
from . import A, atemplate, bundle, conv, flag, util
from . import basic, markdown
from rye_lib import data

BASIC = flag.String('basic', '', 'Test Basic Auth users')

F = fmt.Sprintf

SUBJECT_VERB_OBJECT = regexp.MustCompile(
    '^([0-9]+|[A-Z]+[a-z]+[A-Z][A-Za-z0-9_]*)(([.]+)(([A-Za-z0-9_]+)(([.]+)(([-A-Za-z0-9_.]+)?)?)?)?)?$'
    ).FindStringSubmatch

class WikiParams:
  def __init__(host):
    .host = host
  def SetPath(path):
    pvec = path.split('/')
    while pvec and (pvec[0] == '' or pvec[0].startswith('@')):
      pvec.pop(0)
    say pvec

    .Subject, .Dots, .Verb, .Object, .File = 'HomePage', '', '', '', ''
    if len(pvec) > 0:
      m = SUBJECT_VERB_OBJECT(pvec[0])
      say m
      if not m:
        raise 'Cannot Parse SUBJECT_VERB_OBJECT', pvec[0]
      _, .Subject, _, .Dots, _, .Verb, _, .Dots2, _, .Object = m
      say .Subject, .Dots, .Verb, .Object

    if len(pvec) > 1:
      .File = pvec[1]
      if .File.startswith('.'):
        raise 'Dotfiles Forbidden', .File

    if len(pvec) > 2:
      raise 'Extra junk at end of path.', len(pvec)

    .d = dict(Subject=.Subject, Dots=.Dots, Verb=.Verb, Object=.Object, File=.File)
    say .d
    return self

class AWikiMaster:
  def __init__(aphid, bname, bund=None, users=None):
    .aphid = aphid
    .bname = bname
    must bund
    .bund = bund
    .users = users

    if BASIC.X:  # For Testing
      .users = data.Eval(BASIC.X)

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

    if .users:
      user = basic.CheckBasicAuth(w, r, 'WIKI', .users)
      say user
      if not user:
        return  # Already requested basic auth.
    if .bund.wx:
      wxstuff = basic.GetBasicPw(w, r, 'WebKey-%s' % .bund.bname)
      if not wxstuff:
        return  # Already requested basic auth.
      wxuser, wxpw = wxstuff

    # Our rule is never end in '/' (unless it is exactly path '/').
    say path
    if path.endswith('/') and path != '/':
      say "path.endswith('/')", path
      say r.URL.Path
      urlPath = r.URL.Path.rstrip('/')
      say urlPath
      http.Redirect(w, r, urlPath, http.StatusMovedPermanently)
      return

    wp = WikiParams(host).SetPath(path)

    if wp.File:
      wp.Verb = 'file'
    fn = VERBS.get(wp.Verb)
    if not fn:
      raise 'No such verb: %q' % wp.Verb
    .bund.Link(wxpw)
    with defer .bund.Unlink():
      fn(w, r, self, wp)

def EmitHtml(w, d, t):
  w.Header().Set('Content-Type', 'text/html')
  t.Execute(w, d)

def VerbFile(w, r, m, wp):
  rs, nanos, size = m.bund.NewReadSeekerTimeSize('/wiki/%s/%s' % (wp.Subject, wp.File))
  http.ServeContent(w, r, r.URL.Path, time.Unix(0, nanos), rs)

def VerbDemo(w, r, m, wp):
  try:
    t = bundle.ReadFile(m.bund, '/wiki/%s/__wiki__.txt' % wp.Subject)
  except as ex:
    t = '(Error: %s)' % ex
  d = dict(
      Content = t,
      Title = wp.Subject,
      HeadBox = wp.d['Verb'],
      FootBox = wp.d['Object'],
      Debug = m.bund.ListFiles('wiki')
  )
  say d
  EmitHtml(w, d, atemplate.Demo)

def VerbList(w, r, m, wp):
  if wp.Subject != '0':
    http.Redirect(w, r, "0.list", http.StatusMovedPermanently)
  vec = m.bund.ListDirs('/wiki')
  d = dict(
      List = vec,
      Title = 'List of Pages',
      HeadBox = 'Foo',
      FootBox = 'Foo',
      Debug = [],
  )
  EmitHtml(w, d, atemplate.List)

def VerbView(w, r, m, wp):
  try:
    text = bundle.ReadFile(m.bund, '/wiki/%s/__wiki__.txt' % wp.Subject)
  except:
    # Offer to let them make the page.
    d = dict(
        Title = 'Page does not exist: %q' % wp.Subject,
        Subject = wp.Subject,
        Dots = wp.d['Dots'],
        HeadBox = "",
        FootBox = "",
        Debug = go_wrap(["apple", "banana", "coconut"]),
    )
    EmitHtml(w, d, atemplate.ViewMissing)
    return

  say 'VerbView', text
  _front, _raw_md, html = markdown.ProcessWithFrontMatter(text)
  say 'VerbView', html
  d = dict(
      Html = html,
      Title = wp.Subject,
      HeadBox = wp.d['Verb'],
      FootBox = "THIS IS A VEIW",
      Debug = go_wrap(["apple", "banana", "coconut"]),
  )
  EmitHtml(w, d, atemplate.View)

def VerbEdit(w, r, m, wp):
  text = r.FormValue('text')
  if text:
    # Save it.
    bundle.WriteFile(m.bund, '/wiki/%s/__wiki__.txt' % wp.Subject, text)
    http.Redirect(w, r,
                  "%s%sview" % (wp.Subject, wp.d['Dots']),
                  http.StatusTemporaryRedirect)
    return
  try:
    text = bundle.ReadFile(m.bund, '/wiki/%s/__wiki__.txt' % wp.Subject)
  except:
    text = 'TODO: Edit me!'
  d = dict(
      Text = text,
      Title = "Edit Page %q" % wp.Subject,
      Subject = wp.Subject,
      Dots = wp.Dots,
      Debug = []
  )
  EmitHtml(w, d, atemplate.Edit)

MATCH_FILENAME = regexp.MustCompile('.*filename="([^"]+)"').FindStringSubmatch
def VerbAttach(w, r, m, wp):
  f = None
  if r.Method != "GET":
    r.ParseMultipartForm(1024*1024)
    say r.MultipartForm.File
    say r.MultipartForm.File['file'][0].Header
    cd = r.MultipartForm.File['file'][0].Header.Get('Content-Disposition')
    say cd
    match = MATCH_FILENAME(cd)
    say match
    if match:
      f = match[1]
  say f
  if f:
    # Save it.
    fname = r.MultipartForm.File['file'][0].Filename
    fname = conv.EncodeCurlyStrong(fname)
    fd = r.MultipartForm.File['file'][0].Open()
    stuff = ioutil.ReadAll(fd)
    bundle.WriteFile(m.bund, '/wiki/%s/%s' % (wp.Subject, fname), stuff)
    http.Redirect(w, r,
                  "%s%sview" % (wp.Subject, wp.d['Dots']),
                  http.StatusTemporaryRedirect)
    return
  try:
    stuff = repr(m.bund.ListFiles('/wiki/%s' % wp.Subject))
  except as ex:
    stuff = "ERROR: %q" % ex
  d = dict(
      Text = stuff,
      Title = "Attachments for Page %q" % wp.Subject,
      Subject = wp.Subject,
      Dots = wp.Dots,
      Debug = []
  )
  EmitHtml(w, d, atemplate.Attach)

VERBS = dict(
  demo= VerbDemo,
  list= VerbList,
  view= VerbView,
  edit= VerbEdit,
  attach= VerbAttach,
  file= VerbFile,
)
VERBS[''] = VerbDemo
pass

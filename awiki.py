from go import bytes, bufio, fmt, html/template, net/http, io/ioutil, regexp
from . import atemplate, bundle, markdown

F = fmt.Sprintf

SUBJECT_VERB_OBJECT = regexp.MustCompile(
    '([0-9]+|[A-Z]+[a-z]+[A-Z][A-Za-z0-9_]*)(([.]+)(([A-Za-z0-9_]+)(([.]+)(([-A-Za-z0-9_.]+)?)?)?)?)?$'
    ).FindStringSubmatch

class WikiParams:
  def __init__(host):
    .host = host
  def SetPath(path):
    pvec = path.split('/')
    say pvec
    m = SUBJECT_VERB_OBJECT(pvec[-1])
    say m
    if not m:
      return False

    _, .Subject, _, .Dots, _, .Verb, _, .dots2, _, .Object = m
    say .Subject, .Dots, .Verb, .Object

    .d = dict(Subject=.Subject, Dots=.Dots, Verb=.Verb, Object=.Object)
    say .d
    return self

class AWikiMaster:
  def __init__(bname):
    .bname = bname
    .bund = bundle.Bundles[.bname]

  def Handler4(w, r, host, path):
    if path == '/favicon.ico':
      return

    wp = WikiParams(host).SetPath(path)
    if not wp:
      raise 'Bad WikiParams: %q' % path

    VERBS[wp.Verb](w, r, self, wp)

def EmitHtml(w, d, t):
  w.Header().Set('Content-Type', 'text/html')
  t.Execute(w, d)

def VerbDemo(w, r, m, wp):
  try:
    t = m.bund.ReadFile('/wiki/%s/@wiki' % wp.Subject)
  except as ex:
    t = '(Error: %s)' % ex
  d = dict(
      Content = t,
      Title = wp.Subject,
      HeadBox = wp.d['Verb'],
      FootBox = wp.d['Object'],
      Debug = m.bund.ListFiles('wiki')
  )
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
    text = m.bund.ReadFile('/wiki/%s/@wiki' % wp.Subject)
  except:
    # Offer to let them make the page.
    d = dict(
        Title = 'Page does not exist: %q' % wp.Subject,
        Subject = wp.Subject,
        Dots = wp.d['Dots'],
        HeadBox = "",
        FootBox = "",
        Debug = go_value(["apple", "banana", "coconut"]),
    )
    EmitHtml(w, d, atemplate.ViewMissing)
    return

  say 'VerbView', text
  html = markdown.Process(text)
  say 'VerbView', html
  d = dict(
      Html = html,
      Title = wp.Subject,
      HeadBox = wp.d['Verb'],
      FootBox = "THIS IS A VEIW",
      Debug = go_value(["apple", "banana", "coconut"]),
  )
  EmitHtml(w, d, atemplate.View)

def VerbEdit(w, r, m, wp):
  text = r.FormValue('text')
  if text:
    # Save it.
    m.bund.WriteFile('/wiki/%s/@wiki' % wp.Subject, text)
    http.Redirect(w, r,
                  "%s%sview" % (wp.Subject, wp.d['Dots']),
                  http.StatusTemporaryRedirect)
    return
  try:
    text = m.bund.ReadFile('/wiki/%s/@wiki' % wp.Subject)
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

VERBS = dict(
  demo= VerbDemo,
  list= VerbList,
  view= VerbView,
  edit= VerbEdit,
)
VERBS[''] = VerbDemo
pass

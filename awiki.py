#from go import bytes
#from go import bufio
from go import fmt
from go import io/ioutil
#from go import html/template
from go import regexp
from . import bundle
from . import atemplate

F = fmt.Sprintf

SUBJECT_VERB_OBJECT = regexp.MustCompile(
    '([A-Z]+[a-z]+[A-Z][A-Za-z0-9_]*)(([.]+)(([A-Za-z0-9_]+)(([.]+)(([-A-Za-z0-9_.]+))?)?)??)?$'
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

def BeHtml(w):
  w.Header().Set('Content-Type', 'text/html')

def VerbDemo(w, r, m, wp):
  t = '(Empty.)'
  try:
    fd = m.bund.Open('/wiki/%s/@wiki' % wp.d['Subject'])
    with defer fd.Close():
      t = str(ioutil.ReadAll(fd))
  except as ex:
    t = '(Error: %s)' % ex
  BeHtml(w)
  d = dict(
      Content = t,
      Title = wp.d['Subject'],
      HeadBox = wp.d['Verb'],
      FootBox = wp.d['Object'],
      Debug = m.bund.ListFiles('wiki')
  )
  atemplate.Demo.Execute(w, d)

def VerbView(w, r, m, wp):
  BeHtml(w)
  d = dict(
      Content = repr(wp),
      Title = wp.d['Subject'],
      HeadBox = wp.d['Verb'],
      FootBox = "THIS IS A VEIW",
      Debug = go_value(["apple", "banana", "coconut"]),
  )
  atemplate.View.Execute(w, d)

def VerbEdit(w, r, m, wp):
  BeHtml(w)
  d = dict(
      Content = repr(wp),
      Title = wp.d['Subject'],
      HeadBox = wp.d['Verb'],
      FootBox = "THIS IS A VEIW",
      Debug = []
  )
  atemplate.Edit.Execute(w, d)

VERBS = dict(
  demo= VerbDemo,
  view= VerbView,
  edit= VerbEdit,
)
VERBS[''] = VerbDemo
pass

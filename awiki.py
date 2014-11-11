from go import fmt
from go import html/template
from go import regexp
from . import bundle
from . import atemplate

F = fmt.Sprintf

SUBJECT_VERB_OBJECT = regexp.MustCompile(
    '([A-Z]+[a-z]+[A-Z][A-Za-z0-9_]*)(([.]+)(([A-Za-z0-9_]+)(([.]+)(([-A-Za-z0-9_.]+))?)?)??)?$'
    ).FindStringSubmatch

class AWikiMaster:
  def __init__(bname):
    .bname = bname
    .bund = bundle.Bundles[.bname]

  def Handler4(w, r, host, path):
    if path == '/favicon.ico':
      return

    pvec = path.split('/')
    say pvec
    m = SUBJECT_VERB_OBJECT(pvec[-1])
    say m
    if not m:
      raise 'TODO, redirect to home page'

    _, subj, _, dots, _, verb, _, dotz, _, obj = m
    say subj, dots, verb, obj

    d = dict(subj=subj, dots=dots, verb=verb, obj=obj)

    w.Header().Set('Content-Type', 'text/html')

    DEB = '''<html><body>
<title>{{.subj}}</title>
<h2>{{.subj}}</h2>
<dl>
  <dt>SUBJ = <dd>{{.subj}}
  <dt>DOTS = <dd>{{.dots}}
  <dt>VERB = <dd>{{.verb}}
  <dt>OBJ = <dd>{{.obj}}
</dl>
'''
    t = template.New('DebugTemplate').Parse(DEB)
    # t.Execute(w, d)

    atemplate.T.Execute(w, dict(
        Content = repr(d),
        Title = subj,
        HeadBox = verb,
        FootBox = obj,
    ))

pass

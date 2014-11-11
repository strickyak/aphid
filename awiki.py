from go import regexp
from . import bundle

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
    AWikiSlave(self).Handler4(w, r, host, path)
    
class AWikiSlave:
  def __init__(master):
    .master = master
    .bname = master.bname
    .bund = master.bund

  def Handler4(w, r, host, path):
    pvec = path.split('/')
    say pvec
    m = SUBJECT_VERB_OBJECT(pvec[-1])
    say m
    if not m:
      raise 'TODO, redirect to home page'

    _, subj, _, dots, _, verb, _, dotz, _, obj = m
    say subj, verb, obj

    w.Header().Set('Content-Type', 'text/plain')
    w.Write('subj = %s\r\n', subj)
    w.Write('dots  =%s\r\n', dots)
    w.Write('verb = %s\r\n', verb)
    w.Write('obj = %s\r\n', obj)
    say 'OK'

pass

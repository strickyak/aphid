#from go import github.com/yak-labs/chirp-lang as chirp
#from go import bufio, os, reflect, regexp
#
#from go import github.com/yak-labs/chirp-lang/goapi/default as _
#from go import github.com/yak-labs/chirp-lang/http as _
#from go import github.com/yak-labs/chirp-lang/img as _
#from go import github.com/yak-labs/chirp-lang/posix as _
#from go import github.com/yak-labs/chirp-lang/rpc as _
#from go import github.com/yak-labs/chirp-lang/ryba as _
#
#from . import bundle, markdown, util
#
## Rye Functions to be exported into smilax4.
#RYBA_FUNCTIONS = [
#  bundle.ListDirs,
#  bundle.ListFiles,
#  bundle.ReadFile,
#  bundle.WriteFile,
#  ReadWikiHeadersAndLines,
#  SplitWikiHeadersAndLines,
#  markdown.TranslateMarkdown,
#  ]
#
#NonAlfa = regexp.MustCompile('[^A-Za-z0-9_]+')
#def SimpleFunctionName(f):
#  """Returns the final alphanumeric part of str(f)."""
#  return NonAlfa.ReplaceAllString(str(f), ' ').split()[-1]
#
#def ReadWikiHeadersAndLines(bund, path):
#  return SplitWikiHeadersAndLines(bundle.ReadFile(bund, path))
#
#def SplitWikiHeadersAndLines(contents):
#  state = True
#  headers = {}
#  lines = []
#  for line in str(contents).split('\n'):
#    if state:
#      kv = line.split(' ', 1)
#      say kv, line
#      switch len(kv):
#        case 1:
#          k, = kv
#          if k:
#            headers[k] = ''
#          else:
#            state = False
#        case 2:
#          k, v = kv
#          headers[k] = v
#        default:
#          raise 'Fail', len(kv)
#    else:
#      lines.append(line)
#  return headers, lines 
#
#
#class Smilax4Master:
#  def __init__(aphid, bname, bund, config):
#    .aphid = aphid
#    .bname = bname
#    .bund = bund
#    .config = config
#    .fr = chirp.NewInterpreter()
#
#    say chirp.MkString(.bname)
#    say chirp.MkT(.bund)
#
#    kv = dict(BundName=.bname,
#              Bund=.bund,
#              ).items()
#    for k, v in kv:
#      .fr.SetVar(k, chirp.MkT(v))
#
#    for f in RYBA_FUNCTIONS:
#      fname = SimpleFunctionName(f)
#      say str(f), fname, f
#      #.fr.SetVar('Ryba_' + fname, chirp.MkT(go_cast(ICallV,f)))
#      .fr.SetVar('Ryba_' + fname, chirp.MkT(f))
#      .fr.EvalString('macro %s ARGS { rycall $Ryba_%s {*}$ARGS }' % (fname, fname))
#    say .fr.EvalString("info globals").String()
#    say .fr.EvalString("info commands").String()
#    say .fr.EvalString("info macros").String()
#      
#    boot = bundle.ReadFile(.bund, "/boot/smilax4.tcl")
#    say boot
#    .fr.EvalString(boot)
#    say .fr.EvalString("info globals").String()
#    say .fr.EvalString("info commands").String()
#    say .fr.EvalString("info macros").String()
#
#    for cf in bundle.ListFiles(.bund, "/chunks"):
#      if cf.endswith('.tcl'):
#        say cf
#        src = bundle.ReadFile(.bund, "/chunks/%s" % cf)
#        .fr.EvalString(src)
#        say .fr.EvalString("info globals").String()
#        say .fr.EvalString("info commands").String()
#        say .fr.EvalString("info macros").String()
#
#  def Handle2(w, r):
#    host, extra, path, root = util.HostExtraPathRoot(r)
#    say host, extra, path, root
#
#    try:
#      return .Handle5(w, r, host, path, root)
#    except as ex:
#      say ex
#      print >>w, '<br><br>\n\n*** ERROR *** <br><br>\n\n*** %s ***\n\n***' % ex
#      raise ex
#      return # raise ex
#
#  def Handle5(w, r, host, path, root):
#    r.ParseForm()
#    s = 'list Smilax Four For {%s}' % path
#    print >>w, .fr.Eval(chirp.MkString(str(s)))
#
#    fr = .fr.NewFrame()
#    #fr = .fr.G.Clone().Fr
#    fr.Cred = dict(
#        r=chirp.MkValue(reflect.ValueOf(r)),
#        w=chirp.MkValue(reflect.ValueOf(w)),
#        path=chirp.MkString(r.URL.Path),
#        form=chirp.MkValue(reflect.ValueOf([(k, v) for k, v in r.Form.items()])),
#        )
#    say ";;;;;;;;", fr.Cred
#    say fr.Eval(chirp.MkString("ls"))
#    say fr.Eval(chirp.MkString("Handle"))
#
##say 'Debug--------------'
##chirp.Debug[ord('r')] = True
##chirp.Debug[ord('z')] = True
#
#def SetDebug():
#  native: `
#    i_chirp.Debug['r'] = true
#    i_chirp.Debug['z'] = true
#  `
#SetDebug()
#
#
#pass

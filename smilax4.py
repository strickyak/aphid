from go import github.com/yak-labs/chirp-lang as chirp
from go import bufio, os, reflect, regexp

from go import github.com/yak-labs/chirp-lang/goapi/default as _
from go import github.com/yak-labs/chirp-lang/http as _
from go import github.com/yak-labs/chirp-lang/img as _
from go import github.com/yak-labs/chirp-lang/posix as _
from go import github.com/yak-labs/chirp-lang/rpc as _
from go import github.com/yak-labs/chirp-lang/ryba as _

from . import bundle, util

FUNCTIONS = [
  bundle.ListDirs,
  bundle.ListFiles,
  bundle.ReadFile,
  bundle.WriteFile,
]
NonAlfa = regexp.MustCompile('[^A-Za-z0-9_]+')

class Smilax4Master:
  def __init__(aphid, bname, bund, config):
    .aphid = aphid
    .bname = bname
    .bund = bund
    .config = config
    .fr = chirp.NewInterpreter()

    #go_addr(.fr).SetVar('BundName', chirp.MkString(.bname))
    #go_addr(.fr).SetVar('Bund', chirp.MkT(.bund))

    say chirp.MkString(.bname)
    say chirp.MkT(.bund)

    for f in FUNCTIONS:
      fname = NonAlfa.ReplaceAllString(str(f), ' ').split()[-1]
      say fname, f
      .fr.SetVar(fname, chirp.MkT(f))
      
    kv = dict(BundName=.bname,
              Bund=.bund,
              ).items()
    for k, v in kv:
      .fr.SetVar(k, chirp.MkT(v))

    boot = bundle.ReadFile(.bund, "/boot/smilax4.tcl")
    say boot
    .fr.Eval(chirp.MkString(str(boot)))

    for cf in bundle.ListFiles(.bund, "/chunks"):
      src = bundle.ReadFile(.bund, "/chunks/%s" % cf)
      say cf, src
      .fr.Eval(chirp.MkString(str(src)))

  def Handle2(w, r):
    host, extra, path, root = util.HostExtraPathRoot(r)
    say host, extra, path, root

    try:
      return .Handle5(w, r, host, path, root)
    except as ex:
      say ex
      print >>w, '<br><br>\n\n*** ERROR *** <br><br>\n\n*** %s ***\n\n***' % ex
      raise ex
      return # raise ex

  def Handle5(w, r, host, path, root):
    r.ParseForm()
    s = 'list Smilax Four For {%s}' % path
    print >>w, .fr.Eval(chirp.MkString(str(s)))

    fr = .fr.NewFrame()
    #fr = .fr.G.Clone().Fr
    fr.Cred = dict(
        r=chirp.MkValue(reflect.ValueOf(r)),
        w=chirp.MkValue(reflect.ValueOf(w)),
        path=chirp.MkString(r.URL.Path),
        form=chirp.MkValue(reflect.ValueOf([(k, v) for k, v in r.Form.items()])),
        )
    say ";;;;;;;;", fr.Cred
    say fr.Eval(chirp.MkString("ls"))
    say fr.Eval(chirp.MkString("Handle"))

#say 'Debug--------------'
#chirp.Debug[ord('r')] = True
#chirp.Debug[ord('z')] = True

def SetDebug():
  native: `
    i_chirp.Debug['r'] = true
    i_chirp.Debug['z'] = true
  `
SetDebug()


pass

from go import github.com/yak-labs/chirp-lang as chirp
from go import bufio, os, reflect

from go import github.com/yak-labs/chirp-lang/goapi/default as _
from go import github.com/yak-labs/chirp-lang/http as _
from go import github.com/yak-labs/chirp-lang/img as _
from go import github.com/yak-labs/chirp-lang/posix as _
from go import github.com/yak-labs/chirp-lang/rpc as _
from go import github.com/yak-labs/chirp-lang/ryba as _

from . import bundle, util

native: `
  func ListDirsFunc(bundle_p P, pathname_p P, pw_p P) P {
    return i_bundle.G_3_ListDirs(bundle_p, pathname_p, pw_p)
  }
`
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

    .fr.SetVar('BundName', chirp.MkString(.bname))
    .fr.SetVar('Bund', chirp.MkT(.bund))
    .fr.SetVar('ListDirs', chirp.MkT(bundle.ListDirs))
    .fr.SetVar('ListDirs', chirp.MkT((bundle.ListDirs)))
    .fr.SetVar('ListFiles', chirp.MkT((bundle.ListFiles)))
    .fr.SetVar('ReadFile', chirp.MkT((bundle.ReadFile)))
    .fr.SetVar('WriteFile', chirp.MkT((bundle.WriteFile)))

    boot = bundle.ReadFile(.bund, "boot/smilax4.tcl")
    .fr.Eval(chirp.MkString(str(boot)))

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

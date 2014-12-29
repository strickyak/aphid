# $ LD_LIBRARY_PATH=/usr/local/lib/ rye run Sonnet.py -c=1
# $ LD_LIBRARY_PATH=/usr/local/lib/ rye run Sonnet.py --f=demo.jsonnet.conf 

from go import github.com/strickyak/jsonnet_cgo as J
from . import flag
import sys

def RunFile(filename):
  vm = J.Make()
  with defer vm.Destroy():
    return vm.EvaluateFile(filename)

def RunSnippet(snippet, filename='<SNIPPET>'):
  vm = J.Make()
  with defer vm.Destroy():
    return vm.EvaluateSnippet(filename, snippet)

def main(args):
  C = flag.String('c', '', 'immediate command to run')
  F = flag.String('f', '', 'filename to run')
  flag.Munch(args)
  if C.X:
    print RunSnippet(C.X, '<SNIPPET>')
  elif F.X:
    print RunFile(F.X)
  else:
    print >>sys.stderr, 'Usage:  Sonnet ( -c=COMMAND | -f=FILENAME )'
    sys.exit(2)

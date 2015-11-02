from . import bundle
#from go import github.com/strickyak/redhed
from go import os

# k42 = redhed.NewKey('42', byt(32*'#'))
os.RemoveAll('___redd')
redd = bundle.RedhedBundle(None, 'redd', '___redd', suffix='0', keyid='42', key=byt(16*'pw'))

bundle.WriteFile(redd, '/foo/bar', 'Hello Redd')
must ['foo'] == redd.ListDirs('/')
must ['bar'] == redd.ListFiles('/foo')
revs = redd.ListRevs('/foo/bar')
must len(revs) == 1
must revs[0].startswith('r.')
isDir, theTime, theSize = redd.Stat3('/foo/bar')
must not isDir
must theSize == len('Hello Redd')

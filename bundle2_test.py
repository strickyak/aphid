import bundle
from go import os

pb = bundle.PosixBundle(None, 'posix', '__posix', suffix='0')
s1 = 'Hello Posix Wiki\n'
bundle.WriteFile(pb, '/wiki/HomePage/__wiki__.txt', s1)
s2 = bundle.ReadFile(pb, '/wiki/HomePage/__wiki__.txt')
must s1 == s2

must ['wiki'] == pb.ListDirs('/')
must ['HomePage'] == pb.ListDirs('/wiki')
must [] == pb.ListDirs('/wiki/HomePage')
must ['__wiki__.txt'] == pb.ListFiles('/wiki/HomePage')


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

#########

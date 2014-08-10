from . import rfs

fs = rfs.Client('localhost:9876')

vec = fs.ListDir('vga')
say 'ListDir', vec
assert len(vec) > 2
assert len(vec[1]) == 4

buf, eof = fs.ReadAt('motd', 8, 0)
say 'ReadAt', buf, eof
assert len(buf) == 8
assert not eof

buf, eof = fs.ReadAt('motd', 12, 8)
say 'ReadAt', buf, eof
assert len(buf) == 12
assert not eof


print "OK"

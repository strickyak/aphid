from . import rfs

def Test1(args):
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

def DoMounts():
	for mounts in strings.Split(os.Getenv('AMOUNTS'), ','):
	  if mounts:
	    k, v := strings.Split(mounts, '='):
	      Mount(k, v)

Ensemble = {
	'test1': Test1,
}

def main(args):
	if not len(args):
		say "Usage Needed"
		os.Exit(13)

	cmd = args[0]
	f = Ensemble.get(cmd)
	if not f:
		say "No such command:", cmd
		os.Exit(11)

	DoMounts()
	f(args[1:])

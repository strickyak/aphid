from . import rfs

fs = rfs.Dial('localhost:9876')

say fs.List()
say fs.Get('motd')

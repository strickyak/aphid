from . import rfs

fs = rfs.Client('localhost:9876')

say fs.List('vga')
say fs.Get('motd', 0, 8)
say fs.Get('motd', 8, 99999)

from . import dh

a = dh.Forge('111', 'eleventy-one', dh.G1536)
b = dh.Forge('121', 'twelvety-one', dh.G2048)
c = dh.Forge('131', 'thirteenty-one', dh.G3072)

x = dh.Forge('161', 'sixteenty-one', dh.G1536)
y = dh.Forge('171', 'seventeenty-one', dh.G2048)
z = dh.Forge('181', 'eighteenty-one', dh.G3072)

say a.Public()
say a.Secret()

must a.MutualKey(x.Public()) == x.MutualKey(a.Public())
must b.MutualKey(y.Public()) == y.MutualKey(b.Public())
must c.MutualKey(z.Public()) == z.MutualKey(c.Public())

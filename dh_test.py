import dh

a = dh.Forge(dh.G1536)
b = dh.Forge(dh.G2048)
c = dh.Forge(dh.G3072)

x = dh.Forge(dh.G1536)
y = dh.Forge(dh.G2048)
z = dh.Forge(dh.G3072)

say a.Public()
say a.Secret()

must a.MutualKey(x.Public()) == x.MutualKey(a.Public())
must b.MutualKey(y.Public()) == y.MutualKey(b.Public())
must c.MutualKey(z.Public()) == z.MutualKey(c.Public())

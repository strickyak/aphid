###  I probably have a different laph_test.py in Calif, which I forgot to check in.

from . import laph

e = laph.Engine(' [Abc] a = "foo" [Def] b = "bar" [Ghi.Xyz] ')
e.Parse()
say e.stanzas
say e.stanzas['Abc'].slots['a']
z = laph.Engine('[x] y = ( add 34 "23" )').Parse().stanzas['x'].slots['y']
say z
say z.Show()
assert z.Len() == 3, z

prim_plus__21__2 = laph.List([ laph.Intern('plus'), laph.Lit(21), laph.Lit(2) ])
x = prim_plus__21__2.Eval( [], None )
assert 23 == x.x
assert type(prim_plus__21__2) is laph.List
assert type(x) is laph.Lit
assert type(x.x) is int
say laph.Symbol
say str(laph.Symbol)
say repr(laph.Symbol)

from . import laph2 as L


p1 = '''{ a = {
  x = 5
  y = 10
} }'''
l1 = L.Lex(p1)
say l1.toks
assert l1.toks ==  [
    ("{", 1), ("a", 1), ("=", 1), ("{", 1), (";", 1),
    ("x", 2), ("=", 2), ("5", 2), (";", 2),
    ("y", 3), ("=", 3), ("10", 3), (";", 3),
    ("}", 4), ("}", 4), (";", 4)
    ]

say '####################################################'
t1 = L.Parse(p1).expr()
t1.visit(L.Pass1(), name='/', up=None, root=t1)
say '####################################################'
print t1
say '####################################################'

e = L.Eval() 
z1 = t1.visit(e)
say type(z1)
say z1
assert z1 == {"a": {"x": "5", "y": "10"}}

##########################

print '####################################'
p2 = `{ a = { b = { x = 100 ; c = 5 } } ; d = /a/b { c = 8 } ; e = /a { p = { q = 9 } } }`
t2 = L.Parse(p2).expr()
t2.visit(L.Pass1(), name='/', up=None, root=t2, sup=None)
t2.visit(L.Pass2(), name='/', up=None, root=t2, sup=None)
print t2
z2 = t2.visit(L.Eval())
print z2
assert z2 ==  {"a": {"b": {"c": "5", "x": "100"}}, "d": {"x": "100", "c": "8"}, "e": {"b": {"c": "5", "x": "100"}, "p": {"q": "9"}}}


##########################

print '####################################'
p3 = `{ a = { b = { x = 100 ; c = 5 } } ; d = /a/b { c = 8 } ; e = /a { p = { q = 9 } ; b { x = 888 } } }`
t3 = L.Parse(p3).expr()
t3.visit(L.Pass1(), name='/', up=None, root=t3, sup=None)
t3.visit(L.Pass2(), name='/', up=None, root=t3, sup=None)
print t3
z3 = t3.visit(L.Eval())
print z3
assert z3 == {"a": {"b": {"x": "100", "c": "5"}}, "d": {"c": "8", "x": "100"}, "e": {"b": {"c": "5", "x": "888"}, "p": {"q": "9"}}}

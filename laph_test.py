from . import laph as L
#####################################
p1 = `{ a = { #comment
  x = 5 #comment
  y = 10 #comment
} } #comment `
l1 = L.Lex(p1)
assert l1.toks ==  [
    ("{", 1), ("a", 1), ("=", 1), ("{", 1), (";", 1),
    ("x", 2), ("=", 2), ("5", 2), (";", 2),
    ("y", 3), ("=", 3), ("10", 3), (";", 3),
    ("}", 4), ("}", 4), (";", 4)
    ]
#####################################
p = L.Compile(`{
  a = {
    b = { x = 100 ; y = 200 ; c = 5 }
    bb = { x = 111 ; c = 555 }
  }
  qrs = ?Nando!
  d = /a/b { c = 8 ; z = ( ++ abc $../qrs xyz $x ) }
  e = /a {
    p = { q = 9 } 
    b { x = 888 }
  }
}`)
assert p.Eval('a/b/c') == '5'
assert except p.Eval('a/b/c/x')
assert ["b", "bb", "p"] == p.Keys('/e')
assert ["c", "x"] == p.Keys('/e/bb')
say p.Eval('/')
say p.Eval('/e')
say p.Eval('/e/b')
assert ["c", "x", "y"] == p.Keys('/e/b')
assert "888" == p.Eval('/e/b/x')
assert "100" == p.Eval('/a/b/x')
assert "200" == p.Eval('/e/b/y')
assert "200" == p.Eval('/d/y')
assert "8" == p.Eval('/d/c')
assert "abc?Nando!xyz100" == p.Eval('/d/z')
#---------------------------------
p = L.Compile(`{
  lib = {
    xx = (* $x $x)
    yy = (* $y $y )
    hyp = (+ $xx $yy)
  }
  t1 = /lib {
    x = 3
    y = 4
  }
  result = $/t1/hyp
}`)
assert p.Keys('/lib') == ["hyp", "xx", "yy"]
assert p.Keys('/t1') == ["hyp", "x", "xx", "y", "yy"]
assert "3" == p.Eval('/t1/x')
assert '25' == p.Eval('/result')
#---------------------------------
p = L.Compile(`{
  one = { a = 11 }
  two = one { b = 22 }
  three = two { c = 33 }
  result = (+ $three/a $three/b $three/c )
}`)
assert p.Keys('one') == ['a']
assert p.Keys('two') == ['a', 'b']
assert p.Keys('three') == ['a', 'b', 'c']
assert '66' == p.Eval('result')
#---------------------------------
p = L.Compile(`{
  double = (fn (x) (++ $x $x))
  twice = (fn (x) (+ $x $x))
  count = (range 10)
  doublefoo = ($double foo)
  twice1001 = ($twice 1001)
  doubles = (map $double $count)
  twices = (map $twice $count)
  len2 = (length $twices)
}`)
assert 'foofoo' == p.Eval('doublefoo')
assert '2002' == p.Eval('twice1001')
assert p.Eval('doubles') == ["00", "11", "22", "33", "44", "55", "66", "77", "88", "99"]
assert p.Eval('twices') == ["0", "2", "4", "6", "8", "10", "12", "14", "16", "18"]
assert p.Eval('len2') == "10"
#---------------------------------
print 'OKAY laph2_test'

from . import laph2 as L
#####################################
p1 = `{ a = {
  x = 5
  y = 10
} }`
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

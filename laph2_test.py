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
prog3 = `{
  a = {
    b = { x = 100 ; y = 200 ; c = 5 }
    bb = { x = 111 ; c = 555 }
  } 
  d = /a/b { c = 8 ; z = ( ++ abc qrs xyz ) }
  e = /a {
    p = { q = 9 } 
    b { x = 888 }
  }
}`
tree3 = L.Parse(prog3).expr()
assert L.LazyEval(tree3).Eval('b/c', 'a') == '5'
assert except L.LazyEval(tree3).Eval('b/c/x', 'a')
assert ["b", "bb", "p"] == L.LazyEval(tree3).Eval('/e')
assert ["c", "x"] == L.LazyEval(tree3).Eval('/e/bb')
assert ["c", "x", "y"] == L.LazyEval(tree3).Eval('/e/b')
assert "888" == L.LazyEval(tree3).Eval('/e/b/x')
assert "100" == L.LazyEval(tree3).Eval('/a/b/x')
assert "200" == L.LazyEval(tree3).Eval('/e/b/y')
assert "200" == L.LazyEval(tree3).Eval('/d/y')
assert "8" == L.LazyEval(tree3).Eval('/d/c')
assert "abcqrsxyz" == L.LazyEval(tree3).Eval('/d/z')

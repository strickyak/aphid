from . import laph7 as L
#####################################
#p1 = `{ a = { #comment
#  x = 5 #comment
#  y = 10 #comment
#} } #comment
#`
#l1 = L.Lex(p1)
#assert l1.toks ==  [
#    ("{", 1), ("a", 1), ("=", 1), ("{", 1), (";", 1),
#    ("x", 2), ("=", 2), ("5", 2), (";", 2),
#    ("y", 3), ("=", 3), ("10", 3), (";", 3),
#    ("}", 4), ("}", 4), (";", 4),
#    (";", 5),
#    ]
######################################
#p = L.Compile(`{
#  a = {
#    b = { x = 100 ; y = 200 ; c = 5 }
#    bb = { x = 111 ; c = 555 }
#  }
#  qrs = ?Nando!
#  d = /a/b { c = 8 ; z = ( ++ abc $../qrs xyz $x ) }
#  e = /a {
#    p = { q = 9 } 
#    b { x = 888 }
#  }
#}`)
#assert p.Eval('a/b/c') == '5'
#assert except p.Eval('a/b/c/xyzzy')
#assert ["b", "bb", "p"] == p.Keys('/e')
#assert ["c", "x"] == p.Keys('/e/bb')
#say p.Eval('/')
#say p.Eval('/e')
#say p.Eval('/e/b')
#assert ["c", "x", "y"] == p.Keys('/e/b')
#assert "888" == p.Eval('/e/b/x')
#assert "100" == p.Eval('/a/b/x')
#assert "200" == p.Eval('/e/b/y')
#assert "200" == p.Eval('/d/y')
#assert "8" == p.Eval('/d/c')
#assert "abc?Nando!xyz100" == p.Eval('/d/z')
##---------------------------------
#p = L.Compile(`{
#  lib = {
#    xx = (* $x $x)
#    yy = (* $y $y )
#    hyp = (+ $xx $yy)
#  }
#  t1 = /lib {
#    x = 3
#    y = 4
#  }
#  result = $/t1/hyp
#}`)
#assert p.Keys('/lib') == ["hyp", "xx", "yy"]
#assert p.Keys('/t1') == ["hyp", "x", "xx", "y", "yy"]
#assert "3" == p.Eval('/t1/x')
#assert '25' == p.Eval('/result')
##---------------------------------
#p = L.Compile(`{
#  one = { a = 11 }
#  two = one { b = 22 }
#  three = two { c = 33 }
#  result = (+ $three/a $three/b $three/c )
#}`)
#assert p.Keys('one') == ['a']
#assert p.Keys('two') == ['a', 'b']
#assert p.Keys('three') == ['a', 'b', 'c']
#assert '66' == p.Eval('result')
##---------------------------------
PROGRAM1= `
  a = 100
  b = BART
  c = $b
  d = (* a 314)

  double = (fn (x) (++ $x $x))
  twice = (fn (x) (+ $x $x))
  count = (range 10)
  doublefoo = ($double foo)
  twice1001 = ($twice 1001)
  doubles = (map $double $count)
  twices = (map $twice $count)
  len2 = (length $twices)
  one = (++ (if (<  10 (length $twices)) Is IsNot) < 10)
  two = (++ (if (>= 10 (length $twices)) Is IsNot) >= 10)
  factorial = (fn (n) (if (< $n 2) 1 (* $n ($factorial (- $n 1)))))
  twenty = ($factorial 4)
`
# p = L.Compile(PROGRAM1)
# assert 'foofoo' == p.Eval('doublefoo')
# assert '2002' == p.Eval('twice1001')
# assert p.Eval('doubles') == ["00", "11", "22", "33", "44", "55", "66", "77", "88", "99"]
# assert p.Eval('twices') == ["0", "2", "4", "6", "8", "10", "12", "14", "16", "18"]
# assert p.Eval('len2') == "10"
# assert p.Eval('one') == "IsNot<10"
# assert p.Eval('two') == "Is>=10"
# #NOT YET# assert p.Eval('twenty') == "20"
# #---------------------------------
# print 'OKAY laph2_test'
# #---------------------------------
# #---------------------------------
# #---------------------------------
# #---------------------------------
p1 = L.Compile22(PROGRAM1)
e1 = L.EvalVisitor33(p1)
say e1.visitTuple(p1.tree, '/', '/')
say e1.visitTuple(p1.tree, '/a', '/')
say e1.visitTuple(p1.tree, '/b', '/')
say e1.visitTuple(p1.tree, '/c', '/')
say e1.visitTuple(p1.tree, '/d', '/')

PROGRAM2= `
    a = {
      b = { x = 100 ; y = 200 ; c = 5 ; m = { n = 10 ; nnn = 30 } }
      bb = { x = 111 ; c = 555 }
    }
    qrs = ?Nando!
    d = /a/b { c = 8 ; z = ( ++ abc $../qrs xyz $x ) }
    e = /a {
      p = { q = 9 } 
      b { x = 888 ; m { nn = 20 ; nnn = 40 } }
    }
`

print '###########################\n'
p2 = L.Compile22(PROGRAM2)
print '---------------------------\n'
print PROGRAM2
print ';;;;;;;;;;;;;;;;;;;;;;;;;;;\n'

must ["a", "d", "e", "qrs"] == p2.Eval('/').names
must "?Nando!" == p2.Eval('/qrs').leaf.a
must "100" == p2.Eval('/a/b/x').leaf.a
must "9" == p2.Eval('/e/p/q').leaf.a
must "888" == p2.Eval('/e/b/x').leaf.a
must "200" == p2.Eval('/e/b/y').leaf.a

must "10" == p2.Eval('/a/b/m/n').leaf.a
must None == p2.Eval('/a/b/m/nn')
must "30" == p2.Eval('/a/b/m/nnn').leaf.a

must "10" == p2.Eval('/e/b/m/n').leaf.a
must "20" == p2.Eval('/e/b/m/nn').leaf.a
must "40" == p2.Eval('/e/b/m/nnn').leaf.a

PROGRAM3 = `
  one = { a = 11 }
  two = one { b = 22 }
  three = two { c = 33 }
  result = (+ $three/a $three/b $three/c )
`
p3 = L.Compile22(PROGRAM3)
print '---------------------------\n'
print PROGRAM3
print ';;;;;;;;;;;;;;;;;;;;;;;;;;;\n'
print p3.Eval('/one')
print p3.Eval('/two')
print p3.Eval('/three')
print p3.Eval('/result')

print "OKAY: laph7_test.py"

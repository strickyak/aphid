from . import laph7 as L
from lib import data
#####################################

p1 = `{ a = { #comment
  x = 5 #comment
  y = 10 #comment
} } #comment
`
l1 = L.Lex(p1)
assert l1.toks ==  [
    ("{", 1), ("a", 1), ("=", 1), ("{", 1), (";", 1),
    ("x", 2), ("=", 2), ("5", 2), (";", 2),
    ("y", 3), ("=", 3), ("10", 3), (";", 3),
    ("}", 4), ("}", 4), (";", 4),
    (";", 5),
    ]
######################################

PROGRAM1= `
  a = 100
  b = BART
  c = $b
  d = (* $a 314)

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
p1 = L.Compile22(PROGRAM1)
must "100" == p1.Eval('/a').leaf.a
must "BART" == p1.Eval('/b').leaf.a
must "BART" == p1.Eval('/c').leaf.a
must "31400" == p1.Eval('/d').leaf.a
must "foofoo" == p1.Eval('/doublefoo').leaf.a
must "2002" == p1.Eval('/twice1001').leaf.a
######################################

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
######################################

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
assert '66' == p3.Eval('/result').leaf.a
######################################

PROGRAM4 = `
  _base = { aa = (+ $a $a) }
  one = _base { a = 10 }
  two = one   { a = 22 }
  three = two { a = 33 }
`
p4 = L.Compile22(PROGRAM4)
print '---------------------------\n'
print PROGRAM4
print ';;;;;;;;;;;;;;;;;;;;;;;;;;;\n'
assert '10' == p4.Eval('/one/a').leaf.a
assert '22' == p4.Eval('/two/a').leaf.a
assert '33' == p4.Eval('/three/a').leaf.a
assert '20' == p4.Eval('/one/aa').leaf.a
assert '44' == p4.Eval('/two/aa').leaf.a
assert '66' == p4.Eval('/three/aa').leaf.a


PROGRAM5 = `
  abc = {
    a1 = 110
    a2 = 120
    a3 = 130
    b = { b1 = 210; b2 = 220; d = { d1 = 1111} }
    c = { c1 = 310; c2 = 320; c3 = 330 }
  }

  def = abc {
    a2 = 1120
    c { c3 = 930; c4 = 940 }
  }

  ghi = def {
    a3 = 1130
    b { b2 = 520 ; b3 = 530 ; d { d2 = 2222} }
  }
`
# abc {"a1":"110", "a2":"120", "a3":"130", "b":{"b1":"210", "b2":"220", "d":{"d1":"1111"}}, "c":{"c1":"310", "c2":"320", "c3":"330"}}

# def {"a1":"110", "a2":"1120", "a3":"130", "b":{"b1":"210", "b2":"220", "d":{"d1":"1111"}}, "c":{"c1":"310", "c2":"320", "c3":"930", "c4":"940"}}

# ghi {"a1":"110", "a2":"1120", "a3":"1130", "b":{"b1":"210", "b2":"520", "b3":"530", "d":{"d1":"1111", "d2":"2222"}}, "c":{"c1":"310", "c2":"320", "c3":"930", "c4":"940"}}

p5 = L.Compile22(PROGRAM5)
assert ['d1'] == p5.Eval('/def/b/d').names
assert ['d1', 'd2'] == p5.Eval('/ghi/b/d').names
assert '1111' == p5.Eval('/abc/b/d/d1').leaf.a
assert '1111' == p5.Eval('/def/b/d/d1').leaf.a
assert '1111' == p5.Eval('/ghi/b/d/d1').leaf.a
assert '2222' == p5.Eval('/ghi/b/d/d2').leaf.a
assert p5.Eval('/def/c').names == 'c1 c2 c3 c4'.split()

print "\nabc", p5.ToJson('/abc')
print "\ndef", p5.ToJson('/def')
print "\nghi", p5.ToJson('/ghi')

assert data.Eval(p5.ToJson('/abc')) == {"a1":"110", "a2":"120", "a3":"130", "b":{"b1":"210", "b2":"220", "d":{"d1":"1111"}}, "c":{"c1":"310", "c2":"320", "c3":"330"}}

assert data.Eval(p5.ToJson('/def')) == {"a1":"110", "a2":"1120", "a3":"130", "b":{"b1":"210", "b2":"220", "d":{"d1":"1111"}}, "c":{"c1":"310", "c2":"320", "c3":"930", "c4":"940"}}

assert data.Eval(p5.ToJson('/ghi')) == {"a1":"110", "a2":"1120", "a3":"1130", "b":{"b1":"210", "b2":"520", "b3":"530", "d":{"d1":"1111", "d2":"2222"}}, "c":{"c1":"310", "c2":"320", "c3":"930", "c4":"940"}}

print "OKAY: laph7_test.py"

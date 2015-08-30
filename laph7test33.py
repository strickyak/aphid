from . import laph7 as laph

p1 = `
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

t1 = `{ abc = { a1 = <110> ; a2 = <120> ; a3 = <130> ; b = { b1 = <210> ; b2 = <220> ; d = { d1 = <1111> } } ; c = { c1 = <310> ; c2 = <320> ; c3 = <330> } } ; def = (Derive("abc"): { a2 = <1120> ; c = (Enhance("c"): { c3 = <930> ; c4 = <940> }) }) ; ghi = (Derive("def"): { a3 = <1130> ; b = (Enhance("b"): { b2 = <520> ; b3 = <530> ; d = (Enhance("d"): { d2 = <2222> }) }) }) }`

c1 = laph.Compile22('{' + p1 + '}')
print "######"
print c1.tree
print "######"
must str(c1.tree) == t1

print "######"
for k, v in sorted(c1.look.items()):
  print '%24s = %s' % (k, v)
print "######"

e1 = EvalVisitor33(c1)


print 'OKAY laph1test.py'

from . import chucl3 as C

tree1 = dict(
  negative= ('lambda', ('_x',), ('if', ('<', '$_x', '0'), 'negative', 'positive'), ),
  triangle= ('lambda', ('n',), ('if', ('<', '$n', '2'), '$n', ('+', '$n', ('$triangle', ('-', '$n', '1'))))),
  double= ('lambda', ('_x',), ('+', '$_x', '$_x')),
  x= '1001',
  x1= ('+', '$x', '1'),
  x2= ('+', '$x', '$x'),
  xx= ('++', '$x', '$x'),
  xl= ('$double', '$xx'),
  one = ('$negative', '123'),
  two = ('$negative', '-321'),
  ten = ('$triangle', '4'),
  )

def main(_):
  c = C.Chucl(tree1)

  must c.Find('double') == ('lambda', ('_x',), ('+', '$_x', '$_x'))
  must c.Find('x') == '1001'
  must c.Find('x1') == ('+', '$x', '1')
  must c.Find('x2') == ('+', '$x', '$x')
  must c.Find('xx') == ('++', '$x', '$x')

  must c.Eval('x') == '1001'
  must c.Eval('x1') == '1002'
  must c.Eval('x2') == '2002'
  must c.Eval('xx') == '10011001'
  must c.Eval('xl') == '20022002'
  must c.Eval('one') == 'positive'
  must c.Eval('two') == 'negative'
  must c.Eval('ten') == '10'
  print "OKAY chucl3_test.py"

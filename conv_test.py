from go import unicode.utf8
import conv

big = ''
for i in range(256):
  big += chr(i)

inputs = ['', ' ', '  ', 'a', '\000', '\000\001\000',
          'one two three', byt('one two three'),
          'a b c',
          '\n abc {def} \007 \000 \t',
          '\001', '\000',
          '하나 둘 셋',
          'one 하나 둘two 3셋',
          big, big+big, big+big+big, byt(big+big)]

for s in inputs:
  a = conv.Encode64(s)
  b = conv.Decode64(a)
  assert str(b) == str(s), b, s
  assert byt(b) == byt(s), b, s

  a = conv.EncodeHex(s)
  b = conv.DecodeHex(a)
  assert str(b) == str(s), b, s
  assert byt(b) == byt(s), b, s

  if utf8.ValidString(s):

    a = conv.EncodeCurlyStrong(s)
    b = conv.DecodeCurly(a)
    #say 'STRONG', s, a, b
    must str(s) == b, s, a, b

    a = conv.EncodeCurlyWeak(s)
    b = conv.DecodeCurly(a)
    #say 'WEAK', s, a, b
    must str(s) == b, s, a, b

print "OKAY conv_test.py"

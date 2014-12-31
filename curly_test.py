from . import curly

STRS = [
    'a b c',
    '\n abc {def} \007 \000 \t',
    '',
    '\001',
    '\000',
    '하나 둘 셋',
    'one 하나 둘two 3셋',
    ]

for s in STRS:
  a = curly.StrongCurlyEncode(s)
  b = curly.CurlyDecode(a)
  say 'STRONG', s, a, b
  must s == b

  a = curly.WeakCurlyEncode(s)
  b = curly.CurlyDecode(a)
  say 'WEAK', s, a, b
  must s == b

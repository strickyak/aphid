from go import fmt
from go import os

def HexDump(b, label):
  b = byt(b)
  n = len(b)
  fmt.Fprintf(os.Stderr, "###### %q  len=%d\n", label, n)

  for i in range((n+15)//16):
    y = ''
    z = ''
    for j in range(16):
      k = i*16 + j
      if k < n:
        c = b[k]
        z += '%02x ' % c
        if 32 <= c and c <= 126:
          y += '%c' % c
        else:
          y += '.'
      if j%4 == 3:
        z += ' '
        y += ' '

    fmt.Fprintf(os.Stderr, "### %6d: %-54s %s\n", i*16, z, y)

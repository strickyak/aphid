from go import net
from go import strings

def ServeAnswerOnPort(answer, p):
  quad = [int(s) for s in strings.Split(answer, '.')]
  must 4 == len(quad)
  bind = gonew(net.UDPAddr)
  bind.Port = p
  say "Listening..."
  conn = net.ListenUDP("udp4", bind)
  conn.SetReadBuffer(4096)
  while True:
    buf = byt(400)
    say "Reading..."
    n, addr = conn.ReadFromUDP(buf)
    say n, addr, buf

    assert buf[2] & 128 == 0
    buf[2] = 128  # Response.
    buf[3] = 0    # No recursion.
    assert buf[5] == 1    # One question.
    buf[7] = 1    # One answer.

    assert buf[4] == 0
    assert buf[5] == 1

    i = 12
    while buf[i]:
      n = buf[i]
      say 'Domain Len', n
      for j in range(n):
        say 'Domain Char', buf[1+j]
      i += n + 1
    say 'Domain END'
    i += 5  # Skip END, Type2, Class2.

    i = Put2(i, buf, (192 << 8) | 12 )  # Point to byte 12.
    i = Put2(i, buf, 1)  # Type2 = 1
    i = Put2(i, buf, 1)  # Class2 = 1

    i = Put2(i, buf, 0)  # TTL4 = 60
    i = Put2(i, buf, 60)

    i = Put2(i, buf, 4)  # Len4 = 4
    buf[i], buf[i+1], buf[i+2], buf[i+3] = quad
    buf = buf[:i+4]

    say conn.WriteToUDP(buf, addr)

def Put2(i, buf, x):
  buf[i] = 255 & (x >> 8)
  buf[i+1] = 255 & x
  return i+2

def main(arg):
  ServeAnswerOnPort(arg[0], int(arg[1]))

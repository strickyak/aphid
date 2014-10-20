from go import net
from go import strings
from . import flag
from . import hexdump

BUFLEN = 512

ONE_Q_ONE_A = [0, 1, 0, 1, 0, 0, 0, 0]
LEN_ONE_Q_ONE_A = len(ONE_Q_ONE_A)

def ServeAnswerOnPort(answer, p):
  quad = [int(s) for s in strings.Split(answer, '.')]
  must 4 == len(quad)
  bind = go_new(net.UDPAddr)
  bind.Port = p
  say "Listening..."
  conn = net.ListenUDP("udp4", bind)
  conn.SetReadBuffer(4096)
  while True:
    DoOnce(conn, quad)

def DoOnce(conn, quad):
  try:
    buf = byt(400)
    say "Reading..."
    n, addr = conn.ReadFromUDP(buf)
    say n, addr
    hexdump.HexDump(buf[:n], 'QUESTION from %q' % str(addr))

    must buf[2] & 128 == 0, 'Question byte is', buf[2]
    buf[2] = 128  # Response.
    buf[3] = 0    # No recursion.
    must buf[5] >= 1, 'Num questions is', buf[5]
    for j in range(LEN_ONE_Q_ONE_A):
      buf[j+4] = ONE_Q_ONE_A[j]

    i = 4 + LEN_ONE_Q_ONE_A
    while i < BUFLEN and buf[i]:  # While not len 0, marking End Of Domain Name.
      n = buf[i]
      must n < 65, 'Weird Domain Length Byte:', buf[i], 'at:', i
      i += n + 1
    i += 5  # Skip END, Type2, Class2.

    i = Put2(i, buf, (192 << 8) | 12 )  # Point to byte 12.
    i = Put2(i, buf, 1)  # Type2 = 1
    i = Put2(i, buf, 1)  # Class2 = 1

    i = Put2(i, buf, 0)  # TTL4 = 60
    i = Put2(i, buf, 60)

    i = Put2(i, buf, 4)  # Len4 = 4
    buf[i], buf[i+1], buf[i+2], buf[i+3] = quad
    i += 4
    buf = buf[:i]

    say conn.WriteToUDP(buf, addr)
    hexdump.HexDump(buf[:i], 'ANSWER to %q' % str(addr))

  except as e:
    say 'Caught Exception', e

def Put2(i, buf, x):
  buf[i] = 255 & (x >> 8)
  buf[i+1] = 255 & x
  return i+2

QUAD = flag.String('quad', '127.0.0.1', 'Dotted quad for answer to A record.')
PORT = flag.Int('port', 53, 'UDP port to answer on.')
def main(arg):
  arg = flag.Munch(arg)
  ServeAnswerOnPort(QUAD.X, PORT.X)

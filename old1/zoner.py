# TODO: NXDOMAIN vs No Answer

# NOT SUPPORTED: BOTH "quotes" and (parens) on same line.
# We handle quotes first, then get continuation lines.
# So if quotes are on a continuation line, we will not see it.
# This simplfies the case of parens and semicolons in the quotes,
# which we do handle.

# Demo:
# cat ~/yak/bind/yak/[a-z]*.*[a-z] | p rye run zoner.py  | ../rye/errfilt/errfilt | m
#
# p rye run zoner.py -- -port=9991 yak/zhuk.com  | p ../rye/errfilt/errfilt   | m


from go import strings
from go import regexp
#from go import os
from go import io/ioutil
from go import net
from . import dns
from . import flag
from . import hexdump

PORT = flag.Int('port', 0, 'UDP port to listen on for DNS.')

UDPMAX = 512  # Should be enough bytes for DNS packets.

# [1] is Before the quote, [2] is In the quote, [3] is after.
FindQuote = regexp.MustCompile('^([^;"]*)["]([^"]*)["](.*)$').FindStringSubmatch

# [1] is Before the semicolon.
FindComment = regexp.MustCompile('^([^;]*)[;].*$').FindStringSubmatch

# [1] is first word, [2] is rest.
FindWord = regexp.MustCompile('^([-A-Za-z0-9_.:$@/*]+)\\s*(.*)').FindStringSubmatch

# [1] is rest.
FindWhiteSpace = regexp.MustCompile('^\\s+(.*)').FindStringSubmatch

# [1] ( [2]
FindUnclosedParen = regexp.MustCompile('^([^()]*)[(]([^()]*)$').FindStringSubmatch
# [1] ( [2] ) [3]
FindClosedParen = regexp.MustCompile('^([^()]*)[(]([^()]*)[)]([^()]*)$').FindStringSubmatch

def DropTrailingDot(s):
  if s and len(s) > 1 and s[-1] == '.':
    return s[:-1]
  return s

def ParseBody(d, body, origin):
  ttl = dns.TTL
  current = origin  # Default if no domain in column 1.
  lines = strings.Split(body, '\n')
  i = 0
  n = len(lines)
  while i < n:
    line = lines[i]

    # Try removing quoted from near end of line.
    quoted = []
    while True:
      fq = FindQuote(line)  # Finds first quote.
      if not fq:
        break
      _, front, inside, back = fq
      line = front + ' ' + back
      quoted.append(inside)

    # Try removing semicolon comment.
    fc = FindComment(line)
    if fc:
      _, line = fc

    # Handle open but no close paren.
    fup = FindUnclosedParen(line)
    if fup:
      while not FindClosedParen(line):
        i += 1
        must i < n, ('Missing close paren', line)
        line += lines[i]
        fc = FindComment(line)
        if fc:
          _, line = fc
    fcp = FindClosedParen(line)
    if fcp:
      _, front, middle, _ = fcp
      line = front + ' ' + middle

    # Now we have an entire line.
    orig = line

    # Find first word, which may be missing.
    word1 = current
    fw1 = FindWord(line)
    if fw1:
      _, word1, line = fw1
      if word1 == '@':
        word1 = origin
      if word1[0] != '$':
        current = word1  # Set new default.
    else:
      # If did not remove a first word,
      # we didn't remove any white space either,
      # so do it now.  word1 defaults to current.
      fws = FindWhiteSpace(line)
      if fws:
        _, line = FindWhiteSpace(line)

    words = [word1]
    while True:
      fw = FindWord(line)
      if not fw:
        break
      words.append(fw[1])
      line = fw[2]

    # Anything left over had better be white space.
    fws = FindWhiteSpace(line)
    if fws:
      _, remnant = fws
      line = remnant
    if line:
        raise 'Bad line had remaining stuff', orig, remnant

    # Replace @ with origin.
    words = [(origin if w == '@' else w) for w in words]

    # Special commands, $ORIGIN and $TTL.
    if words[0] == '$ORIGIN':
      say words
      origin = dns.Absolute(words[1], current)
      i += 1
      continue

    if words[0] == '$TTL':
      say words
      ttl = int(words[1])
      i += 1
      continue

    ##### say quoted, words, orig
    rr = dns.MakeRR(words, quoted, current, ttl)
    if rr:
      vec = d.get(rr.name)
      if vec is None:
        vec = []
        d[rr.name] = vec
      vec.append(rr)

    i += 1

  return rr

def Serve(d):
  addy = go_new(net.UDPAddr)
  addy.Port = PORT.X

  say "Listening..."
  conn = net.ListenUDP("udp4", addy)
  conn.SetReadBuffer(4096)

  while True:
    buf = mkbyt(UDPMAX)
    say "ReadingFromUDP..."
    n, addr = conn.ReadFromUDP(buf)
    say n, addr, buf

    go Answer(d, buf, n, addr, conn)

def Answer(d, buf, n, addr, conn):
 try:
  hexdump.HexDump(buf[:n], 'Packet IN')
  q = dns.ReadQuestion(buf, n)
  vec = d.get(q.name)
  if vec:
    buf2 = mkbyt(UDPMAX)
    w = dns.Writer(buf2)
    w.WriteHead1(q.serial, 0)
    na = 0
    for rr in vec:
      if q.typ == 255 or rr.typ == q.typ:
        na += 1
        #if na >= 2:
        #  break
    w.WriteHead2(1, na, 0, 0)
    w.WriteQuestion(q)
    j = 0
    for rr in vec:
      if q.typ == 255 or rr.typ == q.typ:
        rr.WriteRR(w)
        j += 1
        #if j >= 2:
        #  break

    packet = buf2[:w.i]
    hexdump.HexDump(buf[:n], 'Packet IN')
    hexdump.HexDump(packet, 'Packet OUT')
    conn.WriteToUDP(packet, addr)

  pass
 except as ex:
  say 'CAUGHT', ex

def Slurp(d, filename):
  say filename
  origin = strings.Split(filename, '/')[-1]
  say origin
  body = ioutil.ReadFile(filename)
  ParseBody(d, body, origin)

def main(argv):
  filenames = flag.Munch(argv)
  d = {}
  if not filenames:
    raise 'Arguments required for zonefile filenames'
  for filename in filenames:
    Slurp(d, filename)
  Serve(d)

from go import path.filepath
from go import strings
from go import regexp
from go import io.ioutil
from go import net
import bundle
import dns
import flag
import hexdump

UDPMAX = 512  # Should be enough bytes for normal DNS packets.

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

def ParseBody(d, body, origin, self_ip):
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

    # Replace @ with origin, and $SELF with our self_ip address.
    words = [(origin if w == '@' else w) for w in words]
    words = [(self_ip if w == '$SELF' else w) for w in words]

    # Special commands, $ORIGIN and $TTL.
    if words[0] == '$ORIGIN':
      say words
      origin = dns.Absolute(words[1], current)
      say words, origin
      i += 1
      continue

    if words[0] == '$TTL':
      say words
      ttl = int(words[1])
      i += 1
      continue

    say quoted, origin, words, orig
    rr = dns.MakeRR(words, quoted, origin, ttl)
    if rr:
      vec = d.get(rr.name)
      if vec is None:
        vec = []
        d[rr.name] = vec
      vec.append(rr)

    i += 1

  return rr

def Serve(d, bind):
  addy = net.ResolveUDPAddr("udp", bind)

  say "Listening..."
  conn = net.ListenUDP("udp4", addy)
  conn.SetReadBuffer(4096)

  while True:
    buf = mkbyt(UDPMAX)
    say "ReadingFromUDP..."
    n, addr = conn.ReadFromUDP(buf)
    #say n, addr, buf

    go Answer(d, buf, n, addr, conn)

def Just_A_Answers(d, name):
  try:
    vec = d.get(name)
    say 'Just_A_Answers BEFORE STAR', name, vec
    if not vec:
      vec = FindStarRecords(d, name, dns.A4)
    say 'Just_A_Answers WITH STAR', name, vec
    return [rr for rr in vec if rr.typ == dns.A4]
  except:
    return []

def Answer(d, buf, n, addr, conn):
  try:
    hexdump.HexDump(buf[:n], 'Packet IN')
    q = dns.ReadQuestion(buf, n)
    vec = d.get(q.name)
    say 'BEFORE STAR', q.name, vec
    if not vec:
      vec = FindStarRecords(d, q.name, q.typ) + FindStarRecords(d, q.name, dns.CNAME)
    say 'WITH STAR', q.name, vec
    buf2 = mkbyt(UDPMAX)
    w = dns.Writer(buf2)
    if vec:
      na = sum([int(q.typ == 255 or rr.typ == q.typ) for rr in vec])
      w.WriteHead1(q.serial, dns.NO_ERROR)
      if na:
        w.WriteHead2(1, na, 0, 0)
        w.WriteQuestion(q)
        for rr in vec:
          if q.typ == 255 or rr.typ == q.typ:
            rr.WriteRR(w)
      else:
        cvec = d.get(q.name)
        say 'CNAME BEFORE STAR', q.name, cvec
        if not cvec:
          cvec = FindStarRecords(d, q.name, dns.CNAME)
        say 'CNAME WITH STAR', q.name, cvec
        answers = [rr for rr in cvec if rr.typ == dns.CNAME]
        for a in answers:
          answers += Just_A_Answers(d, a.targ)

        if answers:
          w.WriteHead2(1, len(answers), 0, 0)
          w.WriteQuestion(q)
          for c in answers:
            c.WriteRR(w)
        else:
          soa = FindSOA(d, q.name)
          w.WriteHead2(1, 0, int(bool(soa)), 0)
          w.WriteQuestion(q)
          if soa:
            soa.WriteRR(w)
    else:
      soa = FindSOA(d, q.name)
      w.WriteHead1(q.serial, dns.NAME_ERROR)
      w.WriteHead2(1, 0, int(bool(soa)), 0)
      w.WriteQuestion(q)
      if soa:
        soa.WriteRR(w)
    packet = buf2[:w.i]
    hexdump.HexDump(buf[:n], 'Packet IN')
    hexdump.HexDump(packet, 'Packet OUT')
    conn.WriteToUDP(packet, addr)
  except as ex:
    say 'CAUGHT', ex

def FindStarRecords(d, name, typ):
  z = []
  words = name.split('.')
  for i in range(len(words)):
    star_domain = '*.' + '.'.join(words[i:])
    vec = d.get(star_domain)
    if vec:
      for rr in vec:
        if rr.typ == typ:
          c = rr.Clone()
          if not c:
            continue  # Some record types (SOA, NS) cannot be cloned.
          setattrs(c, name=name)
          z.append(c)
      if z:
        return z
  return z

def FindSOA(d, name):
  words = name.split('.')
  for i in range(len(words)):
    subdomain = '.'.join(words[i:])
    vec = d.get(subdomain)
    if vec:
      for rr in vec:
        if rr.typ == dns.SOA:
          return rr

pass

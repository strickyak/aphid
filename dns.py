from go import regexp
from go import strings

# types
A4              = 1 #a host address
NS              = 2 #an authoritative name server
MD              = 3 #a mail destination (Obsolete - use MX)
MF              = 4 #a mail forwarder (Obsolete - use MX)
CNAME           = 5 #the canonical name for an alias
SOA             = 6 #marks the start of a zone of authority
MB              = 7 #a mailbox domain name (EXPERIMENTAL)
MG              = 8 #a mail group member (EXPERIMENTAL)
MR              = 9 #a mail rename domain name (EXPERIMENTAL)
NULL            = 10 #a null RR (EXPERIMENTAL)
WKS             = 11 #a well known service description
PTR             = 12 #a domain name pointer
HINFO           = 13 #host information
MINFO           = 14 #mailbox or mail list information
MX              = 15 #mail exchange
TXT             = 16 #text strings
AXFR            = 252 #A request for a transfer of an entire zone
MAILB           = 253 #A request for mailbox-related records (MB, MG or MR)
MAILA           = 254 #A request for mail agent RRs (Obsolete - see MX)
STAR            = 255 #A request for all records

# classes
IN              = 1 #the Internet
CS              = 2 #the CSNET class (Obsolete - used only for examples in
CH              = 3 #the CHAOS class
HS              = 4 #Hesiod [Dyer 87]

TTL = 111

#     0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                                               |
#   /                                               /
#   /                      NAME                     /
#   |                                               | *
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                      TYPE                     | 2B
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                     CLASS                     | 2B
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ Question stops here.
#   |                      TTL                      |
#   |                                               | 4B
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                   RDLENGTH                    | 2B
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
#   /                     RDATA                     /
#   /                                               / *
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

# name(*) type(2) class(2) ttl(4) rdlen(4) rdata(*)
class ResourceRec:
  def __init__(name, ttl, typ):
    .name = name
    .ttl = ttl
    .typ = typ
    .clas = IN  # Only support IN.

  def WriteRR(w):
    w.WriteDomain(.name)
    w.Write2(.typ)
    w.Write2(.clas)
    w.Write4(.ttl)
    w.StartRData()
    .WriteRData(w)
    w.FinishRData()

class CnameRec(ResourceRec):
  def __init__(name, ttl, targ):
    super(name, ttl, CNAME)
    .targ = targ
  def WriteRData(w):
    w.WriteDomain(.targ)

class A4Rec(ResourceRec):
  def __init__(name, ttl, quad):
    super(name, ttl, A4)
    .quad = [int(x) for x in strings.Split(quad, '.')]
    must len(.quad) == 4
  def WriteRData(w):
    w.WriteQuad(.quad)
  
# primary(*) email(*) serial(4) refresh(4) retry(4) expire(4) minimum(4)
class SoaRec(ResourceRec):
  def __init__(name, ttl, primary, email, serial, refresh, retry, expire, minimum):
    super(name, ttl, SOA)
    .primary = primary
    .email = email
    .serial = int(serial)
    .refresh = int(refresh)
    .retry = int(retry)
    .expire = int(expire)
    .minimum = int(minimum)
  def WriteRData(w):
    w.WriteDomain(.primary)
    w.WriteDomain(.email)
    w.Write4(.serial)
    w.Write4(.refresh)
    w.Write4(.retry)
    w.Write4(.expire)
    w.Write4(.minimum)
  
class NsRec(ResourceRec):
  def __init__(name, ttl, targ):
    super(name, ttl, NS)
    .targ = targ
  def WriteRData(w):
    w.WriteDomain(.targ)

class MxRec(ResourceRec):
  def __init__(name, ttl, pref, targ):
    super(name, ttl, MX)
    .pref = pref
    .targ = targ
  def WriteRData(w):
    w.Write2(.pref)
    w.WriteDomain(.targ)

class TxtRec(ResourceRec):
  def __init__(name, ttl, s):
    super(name, ttl, TXT)
    .s = s
  def WriteRData(w):
    w.WriteString(.s)

#                                    1  1  1  1  1  1
#      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#    |                      ID                       |
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#    |QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#    |                    QDCOUNT                    |
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#    |                    ANCOUNT                    |
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#    |                    NSCOUNT                    |
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#    |                    ARCOUNT                    |
#    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

QR = 1 << 15
AA = 1 << 11
QR_AA = QR | AA

class Writer:
  def __init__(buf):
    .buf = buf
    .i = 0
    #.firstDomain = None
    #.firstOffset = 0
    .domainMap = {}

  def WriteHead1(id, rcode):
    must .i == 0
    .Write2(id)
    .Write2(QR_AA | rcode) # QR=1, AA=1

  def WriteHead2(qu, an, au, ad):
    must .i == 4
    must qu == 1
    .Write2(qu)
    .Write2(an)
    .Write2(au)
    .Write2(ad)

  def WriteQuestion(q):
    .WriteDomain(q.name)
    .Write2(q.typ)
    .Write2(IN)

  def StartRData():
    .mark = .i   # Remember this place; FinishRData will write length here.
    .i += 2      # Skip 2 bytes for that length.

  def FinishRData():
    n = .i - .mark  # Size written since mark in StartRData().
    tmp, .i = .i, .mark  # Temp replace .i with the mark
    .Write2(n)
    .i = tmp  # Restore .i

  def Write4(x):
    .buf[.i+0] = 255 & (x >> 24)
    .buf[.i+1] = 255 & (x >> 16)
    .buf[.i+2] = 255 & (x >> 8)
    .buf[.i+3] = 255 & x
    .i += 4

  def Write2(x):
    .buf[.i] = 255 & (x >> 8)
    .buf[.i+1] = 255 & x
    .i += 2

  def Write1(x):
    .buf[.i] = 255 & x
    .i += 1

  def WriteQuad(quad):
    .buf[.i], .buf[.i+1], .buf[.i+2], .buf[.i+3] = quad
    .i += 4

  def WriteString(s):
    .buf[.i] = len(s)
    .i += 1
    for c in byt(s):
      .buf[.i] = c
      .i += 1

  def WriteDomain(domain):
    p = .domainMap.get(domain)  # Have we seen it?
    if p is not None:
      .Write2(3*64*256 | p)  # Use message compression.
      return

    .domainMap[domain] = .i  # Save current loc for future compression.

    m = DotSplit(domain)
    if m:
      .WriteString(m[1])
      .WriteDomain(m[2])
    else:
      .WriteString(domain)
      .Write1(0)

DotSplit = regexp.MustCompile('^([^.]+)[.](.+)$').FindStringSubmatch

class ReadQuestion:
  def __init__(buf, n):
    .buf = buf
    .serial = .Read2At(0)
    .flags = .Read2At(2)
    if .flags & QR == QR:
      # Not a question.
      return # without setting .name
    .qdCount = .Read2At(4)
    if .qdCount < 1:
      # No question.
      return # without setting .name

    .i = 12  # Skip headers to first RR.
    .name = ''
    while buf[.i]:
      n = buf[.i]
      .i += 1
      b = byt(n)
      for j in range(n):
        b[j] = buf[.i+j]
      if .name:
        .name += '.'
      .name += str(b[:n])
      .i += n
    .i += 1  # Skip END.
    .typ = .Read2At(.i)

  def Read2At(p):
    return (.buf[p] << 8) | .buf[p+1]
    

NUMERIC = regexp.MustCompile('^[0-9]+$').FindString

def Absolute(domain, current):
  if domain[-1] == '.':
    return domain[:-1]
  else:
    return '%s.%s' % (domain, current)
    
def MakeRR(words, quoted, current, ttl):
  say 'MakeRR', ttl
  if len(words) + len(quoted) < 3:
    return None

  domain = Absolute(words[0], current)

  i = 1
  if NUMERIC(words[i]):  # override TTL if number.
    ttl = int(words[i])
    i += 1

  if strings.ToUpper(words[i]) == 'IN':  # Skip IN.
    say '=', ttl
    i += 1

  if strings.ToUpper(words[i]) == 'A':
    quad = words[i+1]
    z = A4Rec(domain, ttl, quad)
    say 'A', domain, quad, z
    return z

  if strings.ToUpper(words[i]) == 'CNAME':
    target = Absolute(words[i+1], current)
    z = CnameRec(domain, ttl, target)
    say 'CNAME', domain, target, z
    return z

  if strings.ToUpper(words[i]) == 'NS':
    target = Absolute(words[i+1], current)
    z = NsRec(domain, ttl, target)
    say 'NS', domain, target, z
    return z

  if strings.ToUpper(words[i]) == 'SOA':
    mname, rname = Absolute(words[i+1], current), Absolute(words[i+2], current)
    serial, refresh, retry, expire, minimum = words[i+3:]
    z = SoaRec(domain, ttl, mname, rname, serial, refresh, retry, expire, minimum)
    say 'SOA', domain, target, z
    return z

  if strings.ToUpper(words[i]) == 'TXT':
    must len(quoted) == 1
    txt = quoted[0]
    z = TxtRec(domain, ttl, txt)
    say 'TXT', domain, target, z
    return z

  if strings.ToUpper(words[i]) == 'MX':
    pref = int(words[i+1])
    target = Absolute(words[i+2], current)
    z = MxRec(domain, ttl, pref, target)
    say 'MX', domain, target, z
    return z

  return None

pass

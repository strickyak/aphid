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
#   |                                               |
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                      TYPE                     |
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                     CLASS                     |
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                      TTL                      |
#   |                                               |
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
#   |                   RDLENGTH                    |
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
#   /                     RDATA                     /
#   /                                               /
#   +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

# name(*) type(2) class(2) ttl(4) rdlen(4) rdata(*)
class ResourceRec:
  def __init__(name, typ):
    .name = name
    .typ = typ
    .clas = IN  # Only support IN.
    .ttl = TTL

  def WriteRR(w):
    w.WriteDomain(.name)
    w.Write2(.typ)
    w.Write2(.clas)
    w.Write4(.ttl)
    w.StartRData()
    .WriteRData(w)
    w.FinishRData()

class CnameRec(ResourceRec):
  def __init__(name, targ):
    super(name, CNAME)
    .targ = targ
  def WriteRData(w):
    w.WriteDomain(.targ)

class A4Rec(ResourceRec):
  def __init__(name, quad):
    super(name, A4)
    .quad = [int(x) for x in strings.Split(quad, '.')]
    must len(.quad) == 4
  def WriteRData(w):
    w.WriteQuad(.quad)
  
# primary(*) email(*) serial(4) refresh(4) retry(4) expire(4) minimum(4)
class SoaRec(ResourceRec):
  def __init__(name, primary, email, serial, refresh, retry, expire, minimum):
    super(name, SOA)
    .primary = primary
    .email = email
    .serial = serial
    .refresh = refresh
    .retry = retry
    .expire = expire
    .minimum = minimum
  def WriteRData(w):
    w.WriteDomain(.primary)
    w.WriteDomain(.email)
    w.Write4(.serial)
    w.Write4(.refresh)
    w.Write4(.retry)
    w.Write4(.expire)
    w.Write4(.minimum)
  
class NsRec(ResourceRec):
  def __init__(name, targ):
    super(name, NS)
    .targ = targ
  def WriteRData(w):
    w.WriteDomain(.targ)

class MxRec(ResourceRec):
  def __init__(name, pref, targ):
    super(name, MX)
    .pref = pref
    .targ = targ
  def WriteRData(w):
    w.Write2(.pref)
    w.WriteDomain(.targ)

class TxtRec(ResourceRec):
  def __init__(name, s):
    super(name, TXT)
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
    say 8888
    .buf = buf
    .i = 0
    say 9999, .buf, .i

  def WriteHead1(id, rcode):
    say 7777, .buf, .i
    must .i == 0
    .Write2(id)
    .Write2(QR_AA | rcode) # QR=1, AA=1

  def WriteHead2(qu, an, au, ad):
    must .i == 4
    must qu == 0  # Don't ask questions.
    .Write2(qu)
    .Write2(an)
    .Write2(au)
    .Write2(ad)

  def StartRData():
    .i += 2
    .mark = .i

  def FinishRData():
    n = .i - .mark
    .Write4At(n, .mark-2)

  def Write4At(x, p):
    .buf[p+0] = 255 & (x >> 24)
    .buf[p+1] = 255 & (x >> 16)
    .buf[p+2] = 255 & (x >> 8)
    .buf[p+3] = 255 & x

  def Write4(x):
    .Write4At(x, .i)
    .i += 4

  def Write2(x):
    say 1111, x, .i, .buf
    .buf[.i] = 255 & (x >> 8)
    .buf[.i+1] = 255 & x
    .i += 2
    say 2222

  def WriteQuad(quad):
    .buf[.i], .buf[.i+1], .buf[.i+2], .buf[.i+3] = quad
    .i += 4

  def WriteString(s):
    for c in byt(s):
      .buf[.i] = c
      .i += 1

  def WriteDomain(domain):
    for word in domain:
      .buf[.i] = len(word)
      .i += 1
      .WriteString(word)
    .buf[.i] = 0
    .i += 1


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
      say 'Domain Len', n
      b = byt(n)
      for j in range(n):
        b[j] = buf[.i+j]
      if .name:
        .name += '.'
      .name += str(b[:n])
      .i += n
    .i += 1  # Skip END.
    .typ = .Read2At(.i)
    say .name, .typ

  def Read2At(p):
    return (.buf[p] << 8) | .buf[p+1]

NUMERIC = regexp.MustCompile('^[0-9]+$').FindString
    
def MakeRR(words quoted):
  if len(words) < 3:
    return None
  domain = 'unknown.domain'  # TODO
  if words[0]:
    domain = words[0]
  i = 1
  if NUMERIC(words[i]):  # Skip TTL
    i += 1
  if words[i] == 'IN':  # Skip IN  # TODO: .upper()
    i += 1
  if words[i] == 'A':  # TODO: .upper()
    return A4Rec(domain, words[i+1])
  return None

pass

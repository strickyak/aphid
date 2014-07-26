from go import net
from go import reflect

class DnsHeader:
  def __init__(self):
    self.id = 0
    self.qr = 0  # Query / Response
    self.opcode = 0
    self.rd = 1  # Recursion Desired
    self.tc = 0  # TrunCation
    self.aa = 0  # Authoritative Answer
    self.ra = 0  # Recursion Available
    self.rcode = 0
    self.qd = []
    self.an = []
    self.ns = []
    self.ar = []

  def FormQuestion(self):
    hdr = byt(12 * '\000')
    say (hdr)
    hdr[0] = 50
    say (hdr)
    hdr[1] = 100
    say (hdr)
    return hdr

def AskDns(server, query):
  svr = reflect.New(gotype(net.UDPAddr)).Interface()
  svr.Port = 53
  svr.IP = net.ParseIP(server)
  # svr.IP = byt( net.ParseIP(server) )
  #svr.IP = gocast(net.IP, net.ParseIP(server))

  u = net.DialUDP("udp", None, svr)
  return u

def main(argv):
  say AskDns("wiki.yak.net", "8.8.8.8")
  say DnsHeader().FormQuestion()

# mango.py -- Encapsulate mangos (pure go implementation of nanomsg).

# Demo:
# mango/mango -buskey=YAK UNO tcp://127.0.0.1:12001 tcp://127.0.0.1:12002
# mango/mango -buskey=YAK DOS tcp://127.0.0.1:12002 tcp://127.0.0.1:12001
# mango/mango -buskey=YAK TRES tcp://127.0.0.1:12003 tcp://127.0.0.1:12001 tcp://127.0.0.1:12002

from go import github.com/gdamore/mangos/protocol/bus
from go import github.com/gdamore/mangos/transport/tcp
from go import time
from . import flag, keyring, sym

PERIOD = 20 * time.Second

class DeDup:
  # Keep a buffer of recent serials, by name.
  # After a period, retire old ones.
  # But remember the highest old retired serial,
  # and never re-admit anything before that.
  #
  # TODO:  Require current session; reject other items.
  #
  # Alternative:  Allow replay attacks, and make sure
  # the messages are only taken as a hint.
  def __init__():
    .d = {}
    go ._GC()

  def _Add(serial):
    must serial
    ts = time.Now()
    site = serial.split('/')[0]
    if site not in .d:
      .d[site] = {}
      .d[site][''] = ''
    .d[site][serial] = ts

  def Check(serial):
    "Return True if it is OK to process this message."
    must serial
    site = serial.split('/')[0]
    d2 = .d.get(site)
    if d2:
      if serial in d2:
        return False
      if serial <= d2['']:
        return False
    ._Add(serial)
    return True

  def _GC():
    while True:
      time.Sleep(PERIOD)
      aboutOnePeriodAgo = time.Now().Add(-1.1 * PERIOD)

      for site, d2 in .d.items():
        min_serial = d2['']
        for ser, ts in d2.items():
          if ser == '':  # Special min key
            continue
          if ts.Before(aboutOnePeriodAgo):
            # Too old.
            # Advance min_serial if ser is greater.
            min_serial = max(min_serial, ser)
            del d2[ser]
        d2[''] = min_serial

DeDupObj = DeDup()

class Bus:
  def __init__(me, my_url, their_urls, handler, key=None):
    .me = me
    .my_url = my_url
    .their_urls = their_urls
    .handler = handler
    must key
    .cipher = sym.Cipher(key)

    .sock = bus.NewSocket()
    .sock.AddTransport(tcp.NewTransport())
    .sock.Listen(my_url)
    for u in their_urls:
      .sock.Dial(u)

    def ReadLoop():
      while True:
        msg = .sock.Recv()
        try:
          opened, serial = .cipher.Open(msg)
          if DeDupObj.Check(serial):
            .handler(opened, serial)
        except as ex:
          say 'CANNOT DECRYPT', ex, msg
    go ReadLoop()

  def Send(msg):
    serial = "%s/%d" % (.me, time.Now().UnixNano())
    sealed = .cipher.Seal(msg, serial)
    .sock.Send(sealed)

def DemoHandler(msg, serial):
  say '@@@@@@@@@@@@@@@@@@@@@ DEMO HANDLE', serial, msg


BUSKEY = flag.String('buskey', '', 'Key ID for Bus')
BUSKEYRING = flag.String('buskeyring', 'test.ring', 'Keyring for Bus')
def main(args):
  args = flag.Munch(args)
  must BUSKEY.X
  ring = {}
  keyring.Load(BUSKEYRING.X, ring)
  say ring.keys()
  keyline = ring[BUSKEY.X]
  key = sym.DecodeHex(keyline.sym)

  name, my_url = args[:2]
  their_urls = args[2:]
  b = Bus(name, my_url, their_urls, DemoHandler, key=key)

  while True:
    time.Sleep(time.Second)
    msg = "%s@%s" % (name, time.Now().Format(time.StampMilli))
    b.Send(msg)

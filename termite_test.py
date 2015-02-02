from go import os, io/ioutil
from . import aphid

TERMITE1 = '''{
  me: 11,

  confname: "termite" + $.me,

  flags: {
    ip:        "127.0.0.1",
    topdir:    "__termite__" + $.confname,
    keyring:   "test.ring",
  },

  peers: {
    "11": { host: "127.0.0.1", port: 8181, name: "termite11" },
    "12": { host: "127.0.0.1", port: 8281, name: "termite12" },
  },

  ports: {
    base::  27000 + ($.me * 100),

    dnsoff::   53,
    httpoff::  80,
    httpsoff::  43,
    rpcoff::   81,

    dns:   self.base + self.dnsoff,
    http:  self.base + self.httpoff,
    https: self.base + self.httpsoff,
    rpc:   self.base + self.rpcoff,
  },

  bundles: {
    "termite0": { kind: "plain" },
    "termite1": { kind: "plain" },
    "termite2": { kind: "sym", key: "YAK" },
    "termite3": { kind: "websym", key: "WLM" },
    "termite3peek": { kind: "websym", key: "BLM" },
  },

  zones: {},
  //zones: {
  //  "aphid.cc": {
  //    "bundle": "termite0",
  //    "zonefile": "dns/aphid.cc",
  //  },
  //},

  webs: {
    "127.0.0.1": { bundle: "termite0" },
    "termite0": { bundle: "termite0" },
    "termite1": { bundle: "termite1" },
    "termite2": { bundle: "termite2" },
    "termite3": { bundle: "termite3" },
  },

  wikis: {
    "localhost": { bundle: "termite0" },
    "wiki": { bundle: "termite0" },
    "web": { bundle: "termite0" },
    "wiki.termite0.aphid.cc": { bundle: "termite0" },
    "termite1.wiki": { bundle: "termite1" },
    "termite2.wiki": { bundle: "termite2" },
    "termite3.wiki": { bundle: "termite3" },
  },
}'''
TERMITE2 = '''import "termite1.conf" {
  me: 12,

  flags: super.flags {
    verbose: 5,
  },

  ports: super.ports {
    debug: self.base + 99,
  },

  webs: super.webs {
    "extra.termite0.aphid.cc": { bundle: "termite0" },
  },

  wikis: super.wikis {
    "extra.wiki.termite0.aphid.cc": { bundle: "termite0" },
  },
}'''

def Clear():
  os.RemoveAll('__termite__11')
  os.RemoveAll('__termite__12')
  os.RemoveAll('__termite__local')
  os.Mkdir('__termite__11')
  os.Mkdir('__termite__12')
  os.MkdirAll('__termite__local/termite0/d.dns/f.aphid.cc', 0777)
  ioutil.WriteFile('__termite__local/termite0/d.dns/f.aphid.cc/r.001.x.1.1', 0666)

def main(_):
  quit = rye_chan(1)
  t1 = aphid.Aphid(quit=quit, filename='termite1.conf', snippet=TERMITE1)
  t2 = aphid.Aphid(quit=quit, filename='termite2.conf', snippet=TERMITE2)
  t1.StartAll()
  t2.StartAll()
  quit.Take()
  say 'QUITTING.'

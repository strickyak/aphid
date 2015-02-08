from go import os, io, io/ioutil
from go import path/filepath as FP
from . import A, aphid, au, sym

TERMITE1 = '''{
  me: 11,

  confname: "termite" + $.me,

  flags: {
    ip:        "127.0.0.1",
    topdir:    "__termite__" + $.confname,
    keyring:   "test.ring",
  },

  peers: {
    "11": { host: "127.0.0.1", port: 28181, name: "termite11" },
    "12": { host: "127.0.0.1", port: 28281, name: "termite12" },
    "13": { host: "127.0.0.1", port: 28381, name: "termite13" },
  },

  ports: {
    base::  $.peers[""+$.me].port - self.rpcoff,

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

  zones: {
    "aphid.cc": {
      "bundle": "termite0",
      "zonefile": "dns/aphid.cc",
    },
  },

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
TERMITE3 = '''import "termite1.conf" {
  me: 13,
  zones: {},
  webs: {},
  wikis: {},
}'''

def Clear():
  for d in ['__termite_local', '__termite__termite11', '__termite__termite12', '__termite__termite13']:
    os.RemoveAll(d)
    os.Mkdir(d, 0777)
    if not d.endswith('local'):
      for b in ['b.termite0', 'b.termite1', 'b.termite2', 'b.termite3']:
        os.Mkdir(FP.Join(d, b), 0777)
    os.Symlink(FP.Join(d, 'b.termite3'), FP.Join(d, 'b.termite3peek')) 

  os.MkdirAll('__termite_local/termite0/dns', 0777)
  ioutil.WriteFile(
      '__termite_local/termite0/dns/aphid.cc',
      'aphid.cc. IN NS cubic.yak.net.\n',
      0666)

def CopyFilesDirToDir(dest, src):
  os.MkdirAll(dest, 0777)
  for f in FP.Glob(FP.Join(src, '*')):
    say f, dest
    b = FP.Base(f)
    r = os.Open(FP.Join(src, b))
    w = os.Create(FP.Join(dest, b))
    io.Copy(w, r)
    w.Close()
    r.Close()

def Cmp(file1, file2):
  say file1
  say file2
  x1 = ioutil.ReadFile(file1)
  x2 = ioutil.ReadFile(file2)
  must x1 == x2

def Glob1(*names):
  vec = FP.Glob(FP.Join('.', *names))
  say names, vec
  must len(vec) == 1
  return vec[0]

def LoadTermite(i):
  for cmd in ['BigLocalDir', 'BigRemoteDir', 'push', 'BigLocalDir', 'BigRemoteDir']:
    say '@@@@@@@@@@@@@@@@@@@@@@@@@', cmd
    # bund = 'termite%d' % i if i<3 else 'termite%dpeek' % i
    bund = 'termite%d' % i
    pw = 'password' if i>2 else ''
    fullcmd = [
        '--bund=%s' % bund, '--dir=./__termite_local', '--server=127.0.0.1:28381',
        '--cid=91', '--sid=92', '--exit=0', '--pw=%s' % pw,
        cmd]
    say '@@@@@@@@@@@@@@@@@@@@@@@@@', fullcmd
    au.main(fullcmd)
    say '@@@@@@@@@@@@@@@@@@@@@@@@@'
    A.Sleep(1)

def main(_):
  Clear()
  quit = rye_chan(1)
  t1 = aphid.Aphid(quit=quit, filename='termite1.conf', snippet=TERMITE1)
  t2 = aphid.Aphid(quit=quit, filename='termite2.conf', snippet=TERMITE2)
  t3 = aphid.Aphid(quit=quit, filename='termite3.conf', snippet=TERMITE3)

  t3.StartAll()
  global Ring
  Ring = t3.ring
  say t3
  say t3.ring
  say Ring

  A.Sleep(1)
  LoadTermite(0)
  A.Sleep(1)
  CopyFilesDirToDir(
      '__termite__termite11/b.termite0/d.dns/f.aphid.cc/',
      '__termite__termite13/b.termite0/d.dns/f.aphid.cc/')
  CopyFilesDirToDir(
      '__termite__termite12/b.termite0/d.dns/f.aphid.cc/',
      '__termite__termite13/b.termite0/d.dns/f.aphid.cc/')

  t1.StartAll()
  A.Sleep(1)
  t2.StartAll()
  A.Sleep(6)

  for i in range(4):
    os.MkdirAll('__termite_local/termite%d/web/frog' % i, 0777)
    ioutil.WriteFile(
        '__termite_local/termite%d/web/frog/index.html' % i,
        'Hello Aphid!\n',
        0666)
    LoadTermite(i)
    A.Sleep(1)
  Cmp(Glob1('__termite__termite13/b.termite0/d.web/d.frog/f.index.html/r.*.13'),
      Glob1('__termite_local/termite0/web/frog/index.html'))
  Cmp(Glob1('__termite__termite13/b.termite0/d.web/d.frog/f.index.html/r.*.13'),
      Glob1('__termite__termite11/b.termite0/d.web/d.frog/f.index.html/r.*.13'))
  Cmp(Glob1('__termite__termite13/b.termite0/d.web/d.frog/f.index.html/r.*.13'),
      Glob1('__termite__termite12/b.termite0/d.web/d.frog/f.index.html/r.*.13'))

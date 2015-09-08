from . import laph7 as L
from lib import data
#####################################

p1 = `{ a = { #comment
  x = 5 #comment
  y = 10 #comment
} } #comment
`
l1 = L.Lex(p1)
assert l1.toks ==  [
    ("{", 1), ("a", 1), ("=", 1), ("{", 1), (";", 1),
    ("x", 2), ("=", 2), ("5", 2), (";", 2),
    ("y", 3), ("=", 3), ("10", 3), (";", 3),
    ("}", 4), ("}", 4), (";", 4),
    (";", 5),
    ]
######################################

PROGRAM1= `
  a = 100
  b = BART
  c = $b
  d = (* $a 314)

  double = (lambda (x) (++ $x $x))
  twice = (lambda (x) (+ $x $x))
  count = (range 10)
  doublefoo = ($double foo)
  twice1001 = ($twice 1001)
  doubles = (map $double $count)
  twices = (map $twice $count)
  len2 = (length $twices)
  one = (++ (if (<  10 (length $twices)) Is IsNot) < 10)
  two = (++ (if (>= 10 (length $twices)) Is IsNot) >= 10)
  factorial = (lambda (n) (if (< $n 2) 1 (* $n ($factorial (- $n 1)))))
  twenty = ($factorial 4)
`
p1 = L.Compile22(PROGRAM1)

must "100" == p1.Eval('/a')
must "BART" == p1.Eval('/b')
must "BART" == p1.Eval('/c')
must "31400" == p1.Eval('/d')

######################################
#must 'Is<10' == p1.Eval('/one').leaf.a
#must 'Is>=10' == p1.Eval('/two').leaf.a
#: must "foofoo" == p1.Eval('/doublefoo').leaf.a
#: must "2002" == p1.Eval('/twice1001').leaf.a
#must "20" == p1.Eval('/twenty').leaf.a
######################################

PROGRAM2= `
    a = {
      b = { x = 100 ; y = 200 ; c = 5 ; m = { n = 10 ; nnn = 30 } }
      bb = { x = 111 ; c = 555 }
    }
    qrs = ?Nando!
    d = /a/b { c = 8 ; z = ( ++ abc $../qrs xyz $x ) }
    e = /a {
      p = { q = 9 } 
      b { x = 888 ; m { nn = 20 ; nnn = 40 } }
    }
`
p2 = L.Compile22(PROGRAM2)
must "D{a,d,e,qrs}" == repr(p2.Eval('/'))
must "?Nando!" == p2.Eval('/qrs')
must "100" == p2.Eval('/a/b/x')
must "9" == p2.Eval('/e/p/q')
must "888" == p2.Eval('/e/b/x')
must "200" == p2.Eval('/e/b/y')

must "10" == p2.Eval('/a/b/m/n')
must None == p2.Eval('/a/b/m/nn')
must "30" == p2.Eval('/a/b/m/nnn')

must "10" == p2.Eval('/e/b/m/n')
must "20" == p2.Eval('/e/b/m/nn')
must "40" == p2.Eval('/e/b/m/nnn')
######################################

PROGRAM3 = `
  one = { a = 11 }
  two = one { b = 22 }
  three = two { c = 33 }
  result = (+ $three/a $three/b $three/c )
`
p3 = L.Compile22(PROGRAM3)
assert '66' == p3.Eval('/result')
######################################

PROGRAM4 = `
  _base = { aa = (+ $a $a) }
  one = _base { a = 10 }
  two = one   { a = 22 }
  three = two { a = 33 }
`
p4 = L.Compile22(PROGRAM4)
assert '10' == p4.Eval('/one/a')
assert '22' == p4.Eval('/two/a')
assert '33' == p4.Eval('/three/a')
assert '20' == p4.Eval('/one/aa')
assert '44' == p4.Eval('/two/aa')
assert '66' == p4.Eval('/three/aa')
######################################

PROGRAM5 = `
  abc = {
    a1 = 110
    a2 = 120
    a3 = 130
    b = { b1 = 210; b2 = 220; d = { d1 = 1111} }
    c = { c1 = 310; c2 = 320; c3 = 330 }
  }

  def = abc {
    a2 = 1120
    c { c3 = 930; c4 = 940 }
  }

  ghi = def {
    a3 = 1130
    b { b2 = 520 ; b3 = 530 ; d { d2 = 2222} }
  }
`
p5 = L.Compile22(PROGRAM5)
assert 'D{d1}' == repr(p5.Eval('/def/b/d'))
assert 'D{d1,d2}' == repr(p5.Eval('/ghi/b/d'))
assert '1111' == p5.Eval('/abc/b/d/d1')
assert '1111' == p5.Eval('/def/b/d/d1')
assert '1111' == p5.Eval('/ghi/b/d/d1')
assert '2222' == p5.Eval('/ghi/b/d/d2')
assert repr(p5.Eval('/def/c')) == 'D{c1,c2,c3,c4}'

assert data.Eval(p5.ToJson('/abc')) == {"a1":"110", "a2":"120", "a3":"130", "b":{"b1":"210", "b2":"220", "d":{"d1":"1111"}}, "c":{"c1":"310", "c2":"320", "c3":"330"}}

assert data.Eval(p5.ToJson('/def')) == {"a1":"110", "a2":"1120", "a3":"130", "b":{"b1":"210", "b2":"220", "d":{"d1":"1111"}}, "c":{"c1":"310", "c2":"320", "c3":"930", "c4":"940"}}

assert data.Eval(p5.ToJson('/ghi')) == {"a1":"110", "a2":"1120", "a3":"1130", "b":{"b1":"210", "b2":"520", "b3":"530", "d":{"d1":"1111", "d2":"2222"}}, "c":{"c1":"310", "c2":"320", "c3":"930", "c4":"940"}}
#################################################

SHEEP = `
hosts = {
  node1 = { num = 31 ; ip = 198.199.119.196 }
  jig1 =  { num = 32 ; ip = 162.243.222.110 }
  lid1 =  { num = 33 ; ip = 208.68.37.161   }
}

_job_template = {
  me = (error YouMustDefineMe)

  confname = (++ sheep_ $me)

  flags = {
    ip =        (error YouMustDefineMe)
    topdir =    (++ /opt/disk/ $confname)
    keyring =   sheep.ring
  }

  peers = {
    31 = { host = $/hosts/node1/ip ; port = 81 ; name = node1 ; num = $/hosts/node1/num ; }
    32 = { host = $/hosts/jig1/ip  ; port = 81 ; name = jig1  ; num = $/hosts/jig1/num  ; }
    33 = { host = $/hosts/lid1/ip  ; port = 81 ; name = lid1  ; num = $/hosts/lid1/num  ; }
  }

  ports = {
    _base =  0

    dns =   (+ $_base 53)
    http =  (+ $_base 80)
    https = (+ $_base 443)
    rpc =   (+ $_base 81)
  }

  bundles = {
    sheep-boxturtle = { kind = plain }
    sheep-dns = { kind = plain }
    sheep-docs = { kind = plain }
    sheep-formic = { kind = plain }
    sheep-smilax = { kind = plain }
    sheep-stash = { kind = plain }
  }

  formic = {
    sheep-formic = { bundle = sheep-formic; paths = { 1 = /@sheep-formic/ } }
    sheep-boxturtle = { bundle = sheep-boxturtle; paths = { 1 = /@sheep-boxturtle/ } }
  }

  smilax4 = {
    sheep-smilax = { bundle = sheep-smilax; paths = { 1 = /@sheep-smilax/ } }
    sheep-docs = { bundle = sheep-docs; paths = { 1 = /@docs/ } }
  }

  stash = {
    sheep-stash = { bundle = sheep-stash; paths = { 1 = /@sheep-stash/ } }
  }

  webs = {}
  wikis =  {}

  zones = {
    aphid.cc = { bundle = sheep-dns ; zonefile = dns/aphid.cc ; }
  }
}

job:node1 = /_job_template {
  me = $/hosts/node1/num
  flags { ip = $/hosts/node1/ip }
}

job:jig1 = /_job_template {
  me = $/hosts/jig1/num
  flags { ip = $/hosts/jig1/ip }
}

job:lid1 = /_job_template {
  me = $/hosts/lid1/num
  flags { ip = $/hosts/lid1/ip }
}

_local_template = /_job_template {
  peers = {
    node1 = { host = 127.0.0.1 ; port = 11081 }
    jig1  = { host = 127.0.0.1 ; port = 12081 }
    lid1  = { host = 127.0.0.1 ; port = 13081 }
  }
  flags { ip = 127.0.0.1 }
}

job:local:node1 = /_local_template {
  me = $/hosts/node1/num
  ports { _base = 11000 }
}

job:local:jig1 = /_local_template {
  me = $/hosts/jig1/num
  ports { _base = 12000 }
}

job:local:lid1 = /_local_template {
  me = $/hosts/lid1/num
  ports { _base = 13000 }
}
`
sheep = L.Compile22(SHEEP)

assert data.Eval(sheep.ToJson('job:node1')) == {"bundles":{"sheep-boxturtle":{"kind":"plain"}, "sheep-dns":{"kind":"plain"}, "sheep-docs":{"kind":"plain"}, "sheep-formic":{"kind":"plain"}, "sheep-smilax":{"kind":"plain"}, "sheep-stash":{"kind":"plain"}},
   "confname":"sheep_31", "flags":{"ip":"198.199.119.196", "keyring":"sheep.ring", "topdir":"/opt/disk/sheep_31"},
   "formic":{"sheep-boxturtle":{"bundle":"sheep-boxturtle", "paths":{"1":"/@sheep-boxturtle/"}}, "sheep-formic":{"bundle":"sheep-formic", "paths":{"1":"/@sheep-formic/"}}},
   "me":"31", "peers":{"31":{"host":"198.199.119.196", "name":"node1", "num":"31", "port":"81"}, "32":{"host":"162.243.222.110", "name":"jig1", "num":"32", "port":"81"}, "33":{"host":"208.68.37.161", "name":"lid1", "num":"33", "port":"81"}},
   "ports":{"dns":"53", "http":"80", "https":"443", "rpc":"81"},
   "smilax4":{"sheep-docs":{"bundle":"sheep-docs", "paths":{"1":"/@docs/"}}, "sheep-smilax":{"bundle":"sheep-smilax", "paths":{"1":"/@sheep-smilax/"}}},
   "stash":{"sheep-stash":{"bundle":"sheep-stash", "paths":{"1":"/@sheep-stash/"}}},
   "webs":{}, "wikis":{}, "zones":{"aphid.cc":{"bundle":"sheep-dns", "zonefile":"dns/aphid.cc"}}}


assert data.Eval(sheep.ToJson('job:jig1')) == {"bundles":{"sheep-boxturtle":{"kind":"plain"}, "sheep-dns":{"kind":"plain"}, "sheep-docs":{"kind":"plain"}, "sheep-formic":{"kind":"plain"}, "sheep-smilax":{"kind":"plain"}, "sheep-stash":{"kind":"plain"}},
   "confname":"sheep_32", "flags":{"ip":"162.243.222.110", "keyring":"sheep.ring", "topdir":"/opt/disk/sheep_32"},
   "formic":{"sheep-boxturtle":{"bundle":"sheep-boxturtle", "paths":{"1":"/@sheep-boxturtle/"}}, "sheep-formic":{"bundle":"sheep-formic", "paths":{"1":"/@sheep-formic/"}}},
   "me":"32", "peers":{"31":{"host":"198.199.119.196", "name":"node1", "num":"31", "port":"81"}, "32":{"host":"162.243.222.110", "name":"jig1", "num":"32", "port":"81"}, "33":{"host":"208.68.37.161", "name":"lid1", "num":"33", "port":"81"}},
   "ports":{"dns":"53", "http":"80", "https":"443", "rpc":"81"},
   "smilax4":{"sheep-docs":{"bundle":"sheep-docs", "paths":{"1":"/@docs/"}}, "sheep-smilax":{"bundle":"sheep-smilax", "paths":{"1":"/@sheep-smilax/"}}},
   "stash":{"sheep-stash":{"bundle":"sheep-stash", "paths":{"1":"/@sheep-stash/"}}},
   "webs":{}, "wikis":{}, "zones":{"aphid.cc":{"bundle":"sheep-dns", "zonefile":"dns/aphid.cc"}}}

assert data.Eval(sheep.ToJson('job:lid1')) == {"bundles":{"sheep-boxturtle":{"kind":"plain"}, "sheep-dns":{"kind":"plain"}, "sheep-docs":{"kind":"plain"}, "sheep-formic":{"kind":"plain"}, "sheep-smilax":{"kind":"plain"}, "sheep-stash":{"kind":"plain"}},
   "confname":"sheep_33", "flags":{"ip":"208.68.37.161", "keyring":"sheep.ring", "topdir":"/opt/disk/sheep_33"},
   "formic":{"sheep-boxturtle":{"bundle":"sheep-boxturtle", "paths":{"1":"/@sheep-boxturtle/"}}, "sheep-formic":{"bundle":"sheep-formic", "paths":{"1":"/@sheep-formic/"}}},
   "me":"33", "peers":{"31":{"host":"198.199.119.196", "name":"node1", "num":"31", "port":"81"}, "32":{"host":"162.243.222.110", "name":"jig1", "num":"32", "port":"81"}, "33":{"host":"208.68.37.161", "name":"lid1", "num":"33", "port":"81"}},
   "ports":{"dns":"53", "http":"80", "https":"443", "rpc":"81"},
   "smilax4":{"sheep-docs":{"bundle":"sheep-docs", "paths":{"1":"/@docs/"}}, "sheep-smilax":{"bundle":"sheep-smilax", "paths":{"1":"/@sheep-smilax/"}}},
   "stash":{"sheep-stash":{"bundle":"sheep-stash", "paths":{"1":"/@sheep-stash/"}}},
   "webs":{}, "wikis":{}, "zones":{"aphid.cc":{"bundle":"sheep-dns", "zonefile":"dns/aphid.cc"}}}

assert data.Eval(sheep.ToJson('job:local:node1')) == {"bundles":{"sheep-boxturtle":{"kind":"plain"}, "sheep-dns":{"kind":"plain"}, "sheep-docs":{"kind":"plain"}, "sheep-formic":{"kind":"plain"}, "sheep-smilax":{"kind":"plain"}, "sheep-stash":{"kind":"plain"}},
  "confname":"sheep_31",
  "flags":{"ip":"127.0.0.1", "keyring":"sheep.ring", "topdir":"/opt/disk/sheep_31"},
  "formic":{"sheep-boxturtle":{"bundle":"sheep-boxturtle", "paths":{"1":"/@sheep-boxturtle/"}}, "sheep-formic":{"bundle":"sheep-formic", "paths":{"1":"/@sheep-formic/"}}},
  "me":"31", "peers":{"31":{"host":"198.199.119.196", "name":"node1", "num":"31", "port":"81"}, "32":{"host":"162.243.222.110", "name":"jig1", "num":"32", "port":"81"}, "33":{"host":"208.68.37.161", "name":"lid1", "num":"33", "port":"81"}, "jig1":{"host":"127.0.0.1", "port":"12081"}, "lid1":{"host":"127.0.0.1", "port":"13081"}, "node1":{"host":"127.0.0.1", "port":"11081"}},
  "ports":{"dns":"11053", "http":"11080", "https":"11443", "rpc":"11081"},
  "smilax4":{"sheep-docs":{"bundle":"sheep-docs", "paths":{"1":"/@docs/"}}, "sheep-smilax":{"bundle":"sheep-smilax", "paths":{"1":"/@sheep-smilax/"}}},
  "stash":{"sheep-stash":{"bundle":"sheep-stash", "paths":{"1":"/@sheep-stash/"}}},
  "webs":{}, "wikis":{}, "zones":{"aphid.cc":{"bundle":"sheep-dns", "zonefile":"dns/aphid.cc"}}}

assert data.Eval(sheep.ToJson('job:local:jig1')) == {"bundles":{"sheep-boxturtle":{"kind":"plain"}, "sheep-dns":{"kind":"plain"}, "sheep-docs":{"kind":"plain"}, "sheep-formic":{"kind":"plain"}, "sheep-smilax":{"kind":"plain"}, "sheep-stash":{"kind":"plain"}},
  "confname":"sheep_32", "flags":{"ip":"127.0.0.1", "keyring":"sheep.ring", "topdir":"/opt/disk/sheep_32"},
  "formic":{"sheep-boxturtle":{"bundle":"sheep-boxturtle", "paths":{"1":"/@sheep-boxturtle/"}}, "sheep-formic":{"bundle":"sheep-formic", "paths":{"1":"/@sheep-formic/"}}},
  "me":"32", "peers":{"31":{"host":"198.199.119.196", "name":"node1", "num":"31", "port":"81"}, "32":{"host":"162.243.222.110", "name":"jig1", "num":"32", "port":"81"}, "33":{"host":"208.68.37.161", "name":"lid1", "num":"33", "port":"81"}, "jig1":{"host":"127.0.0.1", "port":"12081"}, "lid1":{"host":"127.0.0.1", "port":"13081"}, "node1":{"host":"127.0.0.1", "port":"11081"}},
  "ports":{"dns":"12053", "http":"12080", "https":"12443", "rpc":"12081"},
  "smilax4":{"sheep-docs":{"bundle":"sheep-docs", "paths":{"1":"/@docs/"}}, "sheep-smilax":{"bundle":"sheep-smilax", "paths":{"1":"/@sheep-smilax/"}}},
  "stash":{"sheep-stash":{"bundle":"sheep-stash", "paths":{"1":"/@sheep-stash/"}}},
  "webs":{}, "wikis":{}, "zones":{"aphid.cc":{"bundle":"sheep-dns", "zonefile":"dns/aphid.cc"}}}

assert data.Eval(sheep.ToJson('job:local:lid1')) == {"bundles":{"sheep-boxturtle":{"kind":"plain"}, "sheep-dns":{"kind":"plain"}, "sheep-docs":{"kind":"plain"}, "sheep-formic":{"kind":"plain"}, "sheep-smilax":{"kind":"plain"}, "sheep-stash":{"kind":"plain"}},
  "confname":"sheep_33", "flags":{"ip":"127.0.0.1", "keyring":"sheep.ring", "topdir":"/opt/disk/sheep_33"},
  "formic":{"sheep-boxturtle":{"bundle":"sheep-boxturtle", "paths":{"1":"/@sheep-boxturtle/"}}, "sheep-formic":{"bundle":"sheep-formic", "paths":{"1":"/@sheep-formic/"}}},
  "me":"33", "peers":{"31":{"host":"198.199.119.196", "name":"node1", "num":"31", "port":"81"}, "32":{"host":"162.243.222.110", "name":"jig1", "num":"32", "port":"81"}, "33":{"host":"208.68.37.161", "name":"lid1", "num":"33", "port":"81"}, "jig1":{"host":"127.0.0.1", "port":"12081"}, "lid1":{"host":"127.0.0.1", "port":"13081"}, "node1":{"host":"127.0.0.1", "port":"11081"}},
  "ports":{"dns":"13053", "http":"13080", "https":"13443", "rpc":"13081"},
  "smilax4":{"sheep-docs":{"bundle":"sheep-docs", "paths":{"1":"/@docs/"}}, "sheep-smilax":{"bundle":"sheep-smilax", "paths":{"1":"/@sheep-smilax/"}}},
  "stash":{"sheep-stash":{"bundle":"sheep-stash", "paths":{"1":"/@sheep-stash/"}}},
  "webs":{}, "wikis":{}, "zones":{"aphid.cc":{"bundle":"sheep-dns", "zonefile":"dns/aphid.cc"}}}
#############################################

print "OKAY: laph7_test.py"

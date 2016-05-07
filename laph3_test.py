from . import laph3 as L

dd = L.DeepDict()
say dd.guts
say dd.get(('abc', 'def', 'ghi'))

T1 = `
  negative = (lambda (_x) (if (< $_x 0) negative positive))

  triangle = (lambda (n) (if (< $n 2) $n (+ $n ($triangle (- $n 1)))))

  double = (lambda (x) (+ $x $x))
  twice = (lambda (s) (++ $s $s))
  x1 = (+ $x 1)
  x2 = (+ $x $x)
  x = 1001
  xx = (++ $x $x)
  xl = ($double $xx)
  xt = ($twice $xx)

  one = ($negative 123)
  two = ($negative -321)
  ten = ($triangle 4)

  len5 = (len ABCDE)
  map5 = (map (lambda (x) (len $x)) (list a ab abc abcd abcde))
  f5 = (map (lambda (x) (++ $x .)) (filter (lambda (x) (> (len $x) 2)) (list a ab abc abcd abcde)))
  g5 = (map len (filter (lambda (x) (<= 3 (len $x))) (list a ab abc abcd abcde)))
`
def TestT1():
  t = L.Compile(T1)

  must t.Eval('x') == '1001'
  must t.Eval('x1') == '1002'
  must t.Eval('x2') == '2002'
  must t.Eval('xx') == '10011001'
  must t.Eval('xl') == '20022002'
  must t.Eval('one') == 'positive'
  must t.Eval('two') == 'negative'
  must t.Eval('ten') == '10'

  must t.Eval('len5') == '5'
  must t.Eval('map5') == ['1', '2', '3', '4', '5']
  must t.Eval('f5') == ['abc.', 'abcd.', 'abcde.']
  must t.Eval('g5') == ['3', '4', '5']

T2 = `
  _host = {
     type = host
     name = (++ h_ $num)
     ip = (++ 1.2.3. $num)
     _base = (+ 10000 (* 1000 $num))
     addy = (++ $ip : (+ $_base 80))
  }
  h1 = _host { num = 1 }
  h2 = _host { num = 2 }
  h3 = h2 { num = 3 }
  hosts = (list $h1 $h2 $h3)

  hostnames = (map (lambda (x) (get $x name)) $hosts)
  hosts_keys = (map keys $hosts)
  hosts_values = (map values $hosts)
  hosts_items = (map items $hosts)

  # Using reference to host.
  _server = {
    name = (++ server $host/num)
  }
  s1 = _server { host = $h1 }
  s2 = s1 { host = $h2 }
  s3 = s2 { host = $h3 }
  servers = (list $s1 $s2 $s3)
  servernames = (map (lambda (x) (get $x name)) $servers)
  serverhostnames = (map (lambda (x) (get (get $x host) name)) $servers)

  # Using derivation of host.
  _Server = {
    name = (++ Server $host/num)
  }
  S1 = _Server { host = h1 { } }
  S2 = S1 { host = h2 { } }
  S3 = S2 { host = h3 { } }
  Servers = (list $S1 $S2 $S3)
  Servernames = (map (lambda (x) (get $x name)) $Servers)
  Serverhostnames = (map (lambda (x) (get (get $x host) name)) $Servers)


`
def TestT2():
  t = L.Compile(T2)
  must t.Eval('h1/name') == 'h_1'
  must t.Eval('h2/ip') == '1.2.3.2'
  must t.Eval('h3/addy') == '1.2.3.3:13080'
  must t.Eval('h3/type') == 'host'
  must t.Eval('s1/name') == 'server1'
  must t.Eval('s2/name') == 'server2'
  must t.Eval('s3/name') == 'server3'
  must t.Eval('hostnames') == ['h_1', 'h_2', 'h_3']
  must t.Eval('hosts_keys') == 3 * [['addy', 'ip', 'name', 'num', 'type']]
  say t.Eval('hosts_values')
  say t.Eval('hosts_items')

  say t.Eval('servers')
  must t.Eval('servernames') == ['server1', 'server2', 'server3']
  must t.Eval('serverhostnames') == ['h_1', 'h_2', 'h_3']

  say t.Eval('Servers')
  must t.Eval('Servernames') == ['Server1', 'Server2', 'Server3']
  must t.Eval('Serverhostnames') == ['h_1', 'h_2', 'h_3']

def main(_):
  TestT1()
  TestT2()
  print "OKAY laph3_test.py"

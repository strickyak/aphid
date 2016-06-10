from . import laph3 as L

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

  must t.EvalPath('x') == '1001'
  must t.EvalPath('x1') == '1002'
  must t.EvalPath('x2') == '2002'
  must t.EvalPath('xx') == '10011001'
  must t.EvalPath('xl') == '20022002'
  must t.EvalPath('one') == 'positive'
  must t.EvalPath('two') == 'negative'
  must t.EvalPath('ten') == '10'

  must t.EvalPath('len5') == '5'
  must t.EvalPath('map5') == ['1', '2', '3', '4', '5']
  must t.EvalPath('f5') == ['abc.', 'abcd.', 'abcde.']
  must t.EvalPath('g5') == ['3', '4', '5']

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
  must t.EvalPath('h1/name') == 'h_1'
  must t.EvalPath('h2/ip') == '1.2.3.2'
  must t.EvalPath('h3/addy') == '1.2.3.3:13080'
  must t.EvalPath('h3/type') == 'host'
  must t.EvalPath('s1/name') == 'server1'
  must t.EvalPath('s2/name') == 'server2'
  must t.EvalPath('s3/name') == 'server3'
  must t.EvalPath('hostnames') == ['h_1', 'h_2', 'h_3']
  must t.EvalPath('hosts_keys') == 3 * [['addy', 'ip', 'name', 'num', 'type']]
  say t.EvalPath('hosts_values')
  say t.EvalPath('hosts_items')

  say t.EvalPath('servers')
  must t.EvalPath('servernames') == ['server1', 'server2', 'server3']
  must t.EvalPath('serverhostnames') == ['h_1', 'h_2', 'h_3']

  say t.EvalPath('Servers')
  must t.EvalPath('Servernames') == ['Server1', 'Server2', 'Server3']
  must t.EvalPath('Serverhostnames') == ['h_1', 'h_2', 'h_3']

def main(_):
  TestT1()
  # TODO # TestT2()
  print "OKAY laph3_test.py"

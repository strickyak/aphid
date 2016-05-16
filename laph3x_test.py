from . import laph3 as L


t1 = L.Compile(`
  a = bilbo
  b = {
    c = {
      d = frodo
    }
    e = {
      d = samwise
    }
  }
`)

must t1.Resolve('/') == set(['a', 'b'])
must t1.Resolve('/a') == 'bilbo'
must t1.Resolve('/b') == set(['c', 'e'])
must t1.Resolve('/b/c') == set(['d'])
must t1.Resolve('/b/c/d') == 'frodo'

################################

t2 = L.Compile(`
  Q = { a = 111 ; b = 222 }
  R = Q { a = 777 ; c = 888}
`)

must t2.Resolve('/') == set(['Q', 'R'])
must t2.Resolve('/Q') == set(['a', 'b'])
must t2.Resolve('/R') == set(['a', 'b', 'c'])
must t2.Resolve('/Q/a') == '111'
must t2.Resolve('/Q/b') == '222'
must t2.Resolve('/R/a') == '777'
must t2.Resolve('/R/b') == '222'
must t2.Resolve('/R/c') == '888'

################################

t3 = L.Compile(`
  X = {
    M = { a = 111 ; b = 222 }
    N = { c = 333 ; d = 444 }
  }
  Y = X {
    M { a = 555 ; f = 666 }
    P = { z = 888 }
  }
`)

must t3.Resolve('/') == set(['X', 'Y'])
must t3.Resolve('/X') == set(['M', 'N'])
must t3.Resolve('/Y') == set(['M', 'N', 'P'])
must t3.Resolve('/X/M/a') == '111'
must t3.Resolve('/X/M/b') == '222'
must t3.Resolve('/X/N/c') == '333'
must t3.Resolve('/X/N/d') == '444'

must t3.Resolve('/Y/M') == set(['a', 'b', 'f'])
must t3.Resolve('/Y/M/a') == '555'
must t3.Resolve('/Y/M/b') == '222'
must t3.Resolve('/Y/M/f') == '666'
must t3.Resolve('/Y/N/d') == '444'
must t3.Resolve('/Y/P/z') == '888'

################################

t4 = L.Compile(`
  OLD = {
    info = { age = old }
    P = info { size = small }
    Q = P { size = medium }
  }
  NEW = OLD {
    info { age = new }
  }
`)

must t4.Resolve('/NEW/P/size') == 'small'
must t4.Resolve('/NEW/P/age') == 'new'

################################

print 'OKAY laph3_alt.py'

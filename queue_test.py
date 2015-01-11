#from go import github.com/strickyak/aphid

N=123   # Num to count
L=13    # queue Len

class A:
  def __init__(a):
    .a = a

ch = rye_chan(L)
say ch
def Count(n):
  for i in range(n):
    say i
    ch.Put(A(n-i))
  say 'close'
  ch.Close()  # After close, reads will be None.

go Count(N)
z = []
while True:
  x = ch.Take()
  if x is None:   # On None.
    break
  z.append(x.a)

assert z == [N-i for i in range(N)]

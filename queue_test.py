from go import github.com/strickyak/aphid

N=123   # Num to count
L=13    # queue Len

class A:
  def __init__(a):
    .a = a

ch = aphid.NewChan(L)
def Count(n):
  for i in range(n):
    ch.Put(A(n-i))
  ch.Close()  # After close, reads will be None.

go Count(N)
z = []
while True:
  x = ch.Get()
  if x is None:   # On None.
    break
  z.append(x.a)

assert z == [N-i for i in range(N)]

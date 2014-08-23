from go import github.com/strickyak/aphid

N=123   # Num to count
L=13    # queue Len

class A:
  def __init__(a):
    .a = a

q = aphid.NewQueue(L)
def Count(n):
  for i in range(n):
    q.Put(A(n-i))
  q.Close()

go Count(N)
z = []
while True:
  x = q.Get()
  if not x:
    break
  z.append(x.a)

assert z == [N-i for i in range(N)]

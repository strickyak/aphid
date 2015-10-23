from . import queue

#############  Test raw rye_chan.

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
    ch.Send(A(n-i))
  say 'close'
  ch.Close()  # After close, reads will be None.

go Count(N)
z = []
while True:
  x = ch.Recv()
  say x
  if x is None:   # On None.
    break
  z.append(x.a)

assert z == [N-i for i in range(N)]

#############  Test queue.Actor.

z = 0
def MakeAdder(n):
  def adder():
    global z
    z += n
  return adder

a = queue.Actor()
for i in range(101):
  a.Do(MakeAdder(i))
a.Do(None)
a.Wait()
must z == 5050

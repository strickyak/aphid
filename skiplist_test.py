from . import flag
from . import skiplist

class Number:
  def __init__(x):
    .x = x

# Run with no args for a quick test of Skiplist.
# Run with --n="n" to add n trails of abandoned iterator.
N = flag.Int('n', 0, 'Number of trials of abandoned iterator.')
def main(args):
  args = flag.Munch(args)
  # We want sum of (2, 20..29, 200..299)
  want = sum([2*2] + [(x+20)*(x+20) for x in range(10)] + [(x+200)*(x+200) for x in range(100)])
  must want == 6314439  # Checked with C python.

  # First try it with ints as values.
  d = skiplist.SkipList()
  for i in range(1000):
    d.Put(i, i*i)

  must int(d.Get(10)) == 100
  for i in range(1000):
    must int(d.Get(i)) == i*i

  z = 0
  for k, v in d.Items('2'):
    if k == '3':
      break
    z += v
    if k == '2':
      print k, int(v), z
  print z
  must z == want

  # First try it with objects as values.
  d2 = skiplist.SkipList()
  for i in range(1000):
    d2.Put(i, Number(i*i))

  must d2.Get(10).x == 100
  for i in range(1000):
    must d2.Get(i).x == i*i

  z = 0
  for k, v in d2.Items('2'):
    if k == '3':
      break
    z += v.x
    if k == '2':
      print k, repr(v), z
  print z
  must z == want

  # Delete the 3-digit keys starting with 2.
  z = 0
  for k, v in d2.Items('2'):
    if k == '3':
      break
    if len(k) == 3:
      # It seems to be safe to delete as we iterate.
      z += d2.Delete(k).x
  must z == sum([(x+200)*(x+200) for x in range(100)])

  # Now sum the remaining cells.
  z = 0
  for k, v in d2.Items('2'):
    if k == '3':
      break
    z += v.x
  must z == want - sum([(x+200)*(x+200) for x in range(100)])

  print 'skiplist OKAY.'

  z = 0
  i = 0
  while i < N.X:
    i += 1
    for k, v in d2.Items('5'):
      if k == '6':
        break
      z += v.x
    print i, z

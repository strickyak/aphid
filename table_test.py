from go import os
from go import path/filepath as F
from . import table

D ='/tmp/_aphid_test_skiplist_'

try:
  os.RemoveAll(D)
except:
  pass

os.Mkdir(D, 0777)

fd = os.Create(F.Join(D, 't.001'))
print >>fd, '''
# comment
+0012345.0\tcolor\tred
+0012345.0\tflavor\tlime
+0012345.0\tsize\tXL
;
# overrides
+0024680.X\tcolor\tpurple
;
# does not override, too old.
+0012345.!\tflavor\tdurian
;
'''
fd.Close()

t = table.Table(D)
must 'purple' == t.Get('color')
must 'lime' == t.Get('flavor')
must 'XL' == t.Get('size')
must t.Get('bogus') == None

t.Set('color', 'pink')
t.Set('flavor', 'lychee')

t2 = table.Table(D)
must 'pink' == t.Get('color')
must 'lychee' == t.Get('flavor')
must 'XL' == t.Get('size')
must t.Get('bogus') == None
pass

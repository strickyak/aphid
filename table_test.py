from go import os
from go import path.filepath as F
import table

D ='/tmp/_aphid_test_skiplist_'

try:
  os.RemoveAll(D)
except:
  pass

os.Mkdir(D, 0777)

fd = os.Create(F.Join(D, 't.001'))
print >>fd, '''
# comment
+0012345.0{tab}color{tab}red
+0012345.0{tab}flavor{tab}lime
+0012345.0{tab}size{tab}XL
;
# overrides
+0024680.X{tab}color{tab}purple
;
# does not override, too old.
+0012345.!{tab}flavor{tab}durian
;
'''.format(tab='\t')
fd.Close()

t = table.Table(D)
must 'purple' == t.Get('color')
must 'lime' == t.Get('flavor')
must 'XL' == t.Get('size')
must t.Get('bogus') == None

t.Put('color', 'pink')
t.Put('flavor', 'lychee')

t2 = table.Table(D)
must 'pink' == t.Get('color')
must 'lychee' == t.Get('flavor')
must 'XL' == t.Get('size')
must t.Get('bogus') == None
pass

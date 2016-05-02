from . import laph3 as L

dd = L.DeepDict()
dd.put(('abc', 'def', 'ghi'), 'yak')
say dd.guts
say dd.get(('abc', 'def', 'ghi'))

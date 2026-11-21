import sys,runpy,http.client
from unittest.mock import patch
source,target=sys.argv[1:];original=http.client.HTTPSConnection
def probe(*a,**kw):
 original('example.invalid',443,timeout=1).close()
 assert http.client.HTTPSConnection is original
 return {}
with patch.object(sys,'argv',[source,target]),patch.object(runpy,'run_path',side_effect=probe):
 exec(compile(open(source).read(),source,'exec'),{'__name__':'observer'})
print('constructor PASS')

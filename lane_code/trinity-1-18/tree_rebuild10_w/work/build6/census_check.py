import json,os,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/'work/build6'))
from compact_tmp import inventory,native_inventory
os.environ['R2_FAST_CENSUS']='0';t=time.monotonic();a=inventory(L/'work/tmp');slow=time.monotonic()-t
t=time.monotonic();b=native_inventory((L/'work/tmp').resolve());fast=time.monotonic()-t
record=dict(equal=a==b,files=len(a),bytes=sum(a.values()),python_seconds=slow,native_seconds=fast,
            command=['/usr/bin/find','work/tmp','-type','f','-printf','file size and path separated by NUL'],
            semantics='Regular files only; no symbolic-link traversal; logical byte sizes; same exact inventory for cap and compaction.')
(L/'work/build6/CENSUS_EQUIVALENCE.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));assert a==b

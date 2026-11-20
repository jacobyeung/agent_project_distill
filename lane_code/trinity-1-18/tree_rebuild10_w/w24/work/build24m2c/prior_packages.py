from common import *
import time
records={}
for name,expected in J.load(L/'work/build24m2/BASELINE.json')['packages'].items():
 path=L/'out'/name;h=hashlib.sha256();start=time.monotonic();count=0
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):
   h.update(block);count+=len(block)
   time.sleep(max(0,count/4_000_000-(time.monotonic()-start)))
 assert dict(sha256=h.hexdigest(),bytes=count)==expected,name
 records[name]=expected;print(name,'unchanged',flush=True)
J.write(D/'PRIOR_PACKAGES.json',dict(status='PASS',packages=records,read_rate_bytes_per_second=4_000_000))

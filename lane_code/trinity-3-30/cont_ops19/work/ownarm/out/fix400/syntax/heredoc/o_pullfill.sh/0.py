import hashlib,json,sys,tarfile,re
from pathlib import Path
p=Path(sys.argv[1]);e=Path(sys.argv[2])
with tarfile.open(p/'0.tgz') as t:b=json.load(t.extractfile('9.json'))['export_binding']
f=(e/'5').read_text().split()
assert len(f)==3 and f[0]==b['object'] and f[1].isdigit() and int(f[1])>0 and re.fullmatch('[0-9a-f]{64}',f[2])
assert int(f[1])==21583032320 and f[2]=='dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5', 'Completion receipt differs from the reviewed export'
for key,name in [('config','7'),('receipt','8'),('data_receipt','9')]:
 assert hashlib.sha256((e/name).read_bytes()).hexdigest()==b['preparation_sha256'][key]
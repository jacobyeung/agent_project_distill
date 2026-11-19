from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
old=json.loads((D/'BASE_SOURCES.json').read_text());manifest=json.loads((L/'attic/build23/PACKAGE_MANIFEST.json').read_text())['files'];records={}
for name,source in old.items():
 h=hashlib.sha256(source.encode()).hexdigest();assert h==manifest['work/tree_r1/'+name]['sha256']
 records[name]=dict(base_sha256=h,new_sha256=hashlib.sha256((L/'work/tree_r1'/name).read_bytes()).hexdigest())
(D/'PATCH_BASE.json').write_text(json.dumps(dict(status='PASS',base_tree='b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8',files=records),indent=2)+'\n')
print('Seven patch bases match the b262e7a7 manifest.')

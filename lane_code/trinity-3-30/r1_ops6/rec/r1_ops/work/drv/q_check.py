import hashlib,json,subprocess,sys
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_@STORE@');H=B.parent/'x_3fdda0fb'
N=B.parent/'i_1be16f28/q_6c18a2bf/o'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert sha(N/'q.json')=='e48ab85bb9364aab228da7b23033605935e384761f76b0e6527c5e221b1c14b4'
assert sha(N/'native/receipt.json')=='2e25a01d943cc910f58260255ae5d2943fbbee2b7114f7d86e280c509e321f68'
r=load(N/'q.json');assert r['status']=='EQUAL' and r['regenerated'] is True
assert r['differences']==[] and r['raw_differences']==[] and all(v['equal'] for v in r['indices'].values())
assert sha(N/'r.json')==r['selection_sha256']==sha(H/'k/pool_selection_eac5f9f0.json')
assert not (B/'q').exists(), 'q already exists'
subprocess.run([sys.executable,'-B',str(B/'q.py'),'--parent',str(H/'k/pool_selection_eac5f9f0.json'),'--indices',str(H/'k'),'--native-receipt',str(N/'native/receipt.json'),'--implementation',str(B/'j.json'),'--code-record',str(B/'c.json'),'--out',str(B/'q')],check=True)
p=load(B/'q/q.json');assert p['status']=='PASS' and p['native_regeneration_executed'] is True
assert p['selection_sha256']==load(B/'BINDING.json')['selection_sha256']==sha(B/'q/r.json')==sha(B/'s.json')
print('PASS native receipt reused; ordered indices checked; projection',p['selection_sha256'])

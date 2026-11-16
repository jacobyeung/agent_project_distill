import json,csv,hashlib,sys
W='/scratch/jjyeung/orch_n30/k1_ops3/work/'
P=json.load(open(W+'gt_sets/GT_SET_PRIMARY_296.json'));S=json.load(open(W+'gt_sets/GT_SET_SENSITIVITY_300.json'))
rows=list(csv.DictReader(open(W+'RASTER_PLACEMENT.tsv'),delimiter='\t'))
from collections import Counter
print('tsv rows',len(rows),Counter(r['status'] for r in rows))
M=json.load(open(W+'codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
print('manifest sha',hashlib.sha256(open(W+'codex_arkit_timing/K1_MANIFEST.arkit_timing.json','rb').read()).hexdigest()[:8])
mc={c['canonical']:c for c in M['captures']};print('manifest captures',len(mc))
bad=0
for r in rows:
  k=r['canonical'];c=mc[k]
  if r['status']=='copied':
    p=P.get(k)
    ok=p and p['pinned'] is True and p['sha256']==r['pin']==c['gt']['sha256'] and p['path']==r['target']==c['gt']['path'] and S[k]==p
    if not ok:bad+=1;print('BAD',k,p,r)
  else:
    s=S.get(k)
    ok=k not in P and s and s['pinned'] is False and r['pin']==c['gt']['sha256']
    print('unpinned',k,r['status'],s and {x:s[x] for x in s if x!='path'},s and s['path'],'manifest pin',c['gt']['sha256'][:8])
    if not ok:bad+=1;print('BAD',k)
print('P',len(P),'S',len(S),'S-P',sorted(set(S)-set(P)),'P-S',set(P)-set(S),'bad',bad,'manifest-S',set(mc)-set(S))
# file hashes on disk
n=0
for k,s in S.items():
  h=hashlib.sha256(open(s['path'],'rb').read()).hexdigest()
  if h!=s['sha256']:print('DISK MISMATCH',k);n+=1
print('disk mismatches',n)

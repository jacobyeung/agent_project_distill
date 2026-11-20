U=/project/community/jjyeung/okh7/x_22c714e1/u; date -u +%TZ; ls -la $U/634820b4* 2>&1 | head -2
python3 -I -s -B - <<'PY'
import json,os
U='/project/community/jjyeung/okh7/x_22c714e1/u'
d=json.load(open(U+'/969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986')); m=json.load(open(U+'/a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'))
wp=U+'/634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed'; w=json.load(open(wp)) if os.path.exists(wp) else None
print('P dev keys',{k:(len(v) if hasattr(v,'__len__') else v) for k,v in d.items()})
print('merged keys',{k:(len(v) if hasattr(v,'__len__') else v) for k,v in m.items()})
for k in ('rule','schema'): print(k,'equal',d.get(k)==m.get(k))
R=set(m['rooms'])-set(d['rooms']); print('rooms: P subset of merged',set(d['rooms'])<=set(m['rooms']),'added',len(R),sorted(R)[:6])
G=set(m['physical_groups'])-set(d['physical_groups']); print('groups: subset',set(d['physical_groups'])<=set(m['physical_groups']),'added',len(G),sorted(G)[:4])
A=set(m['aliases'])-set(d['aliases']); print('alias keys subset',set(d['aliases'])<=set(m['aliases']),'added',len(A))
print('P alias values preserved',all(set(v)<=set(m['aliases'][k]) for k,v in d['aliases'].items()))
print('natives subset',set(d['natives'])<=set(m['natives']),'added',len(set(m['natives'])-set(d['natives'])))
if w:
    wr=set(w['rooms']); print('withheld rooms',len(wr),'== added groups',wr==G, sorted(wr)[:3])
    wa={a for v in w['aliases'].values() for a in v}; print('added natives == withheld alias values', (set(m['natives'])-set(d['natives']))<=wa, len(wa))
PY

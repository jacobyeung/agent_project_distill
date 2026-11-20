X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173703; date -u +%TZ; sha256sum $O/na.json.gz $O/rd0/rdiff.json.gz
nice -n 10 python3 -I -s -B - <<'PY'
import json,gzip,collections
X='/project/community/jjyeung/okh7/x_22c714e1'; O=X+'/o/173703'; U=X+'/u/'
m=json.load(open(U+'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5')); d=json.load(open(U+'969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'))
def names(x):
    s=set(x['natives'])|set(x['rooms'])|set(x['aliases'])
    for v in x['aliases'].values(): s|=set(v)
    for v in x['canonical'].values(): s|=set(v)
    return s
M=names(m); Dn=names(d); print('name sets',len(M),len(Dn), sorted(M)[:4])
rd=json.load(gzip.open(O+'/rd0/rdiff.json.gz')); na=json.load(gzip.open(O+'/na.json.gz'))['rows']
A={e['i']:e for e in rd['P_absent']}
c=collections.Counter()
for r in na:
    e=A.get(r['i']); c['na']+=1; c['in_rdiff_absent_same_key']+= e is not None and e['key']==r['key']
    s=r['key'][0]+'/'+r['key'][1]; c['scene_in_merged']+= s in M; c['scene_in_P_dev']+= s in Dn; c['unlisted_both']+= (not r['removal_list_sha256s']) and (not e['removal_list_sha256s'])
unl=[e for e in rd['P_absent'] if not e['removal_list_sha256s']]; c['rdiff_unlisted']=len(unl); c['na_covers_all_unlisted']= set(e['i'] for e in unl)==set(r['i'] for r in na)
kept=collections.Counter((e['key'][0]+'/'+e['key'][1]) in M for e in rd['N']); c['kept_in_merged']=kept[True]; c['kept_not_in_merged']=kept[False]
print(dict(c)); print('example names in merged for misses',[r['key'][:2] for r in na if r['key'][0]+'/'+r['key'][1] not in M][:5])
PY

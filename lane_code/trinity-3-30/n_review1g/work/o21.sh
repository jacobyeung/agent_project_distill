X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173881; U=$X/u; TZ=UTC date +%TZ; df -h /project/community | tail -1
ls $O | tr '\n' ' '; echo; ls $O/rd0 2>&1 | tr '\n' ' '; echo
sha256sum $X/rdiff.py $O/rdiff.py $X/jd6.sh $X/dbb3.py $O/na.json.gz $O/rd0/rdiff.json.gz $O/nd.json $O/routing_selection.json $O/chain.json 2>&1 | cut -c1-140
grep -n 'SBATCH -p\|job-name' $X/jd6.sh
nice -n 10 python3 -I -s -B - <<'PY'
import json,gzip,collections
X='/project/community/jjyeung/okh7/x_22c714e1'; O=X+'/o/173881'; U=X+'/u/'
m=json.load(open(U+'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5')); d=json.load(open(U+'969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986'))
def names(x):
    s=set(x['natives'])|set(x['rooms'])|set(x['aliases'])
    for v in x['aliases'].values(): s|=set(v)
    for v in x['canonical'].values(): s|=set(v)
    return s
M=names(m); Dn=names(d); print('name sets',len(M),len(Dn))
rd=json.load(gzip.open(O+'/rd0/rdiff.json.gz')); na=json.load(gzip.open(O+'/na.json.gz'))['rows']
A={e['i']:e for e in rd['P_absent']}
c=collections.Counter(); L=collections.Counter()
for r in na:
    e=A.get(r['i']); c['na']+=1; c['in_rdiff_absent_same_key']+= e is not None and e['key']==r['key']
    s=r['key'][0]+'/'+r['key'][1]; c['scene_in_merged']+= s in M; c['scene_in_P_dev']+= s in Dn
    if s not in M:
        for h in (r.get('removal_list_sha256s') or []): L[h[:8]]+=1
        c['not_in_merged']+=1; c['not_in_merged_listed']+= bool(r.get('removal_list_sha256s'))
c['P_absent_total']=len(rd['P_absent'])
unl=[e for e in rd['P_absent'] if not e['removal_list_sha256s']]; c['rdiff_unlisted']=len(unl)
lis=[e for e in rd['P_absent'] if e['removal_list_sha256s']]; c['rdiff_listed']=len(lis)
c['listed_lists']=str(collections.Counter(h[:8] for e in lis for h in e['removal_list_sha256s']))
c['unlisted_scene_in_merged']=sum((e['key'][0]+'/'+e['key'][1]) in M for e in unl)
kept=collections.Counter((e['key'][0]+'/'+e['key'][1]) in M for e in rd['N']); c['kept_in_merged']=kept[True]; c['kept_not_in_merged']=kept[False]
print(dict(c)); print('lists of na rows not in merged',dict(L))
# third control row
p=U+'15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022'
op=gzip.open if open(p,'rb').read(2)==b'\x1f\x8b' else open
n=0
for line in op(p,'rt'):
    if 'vsi590k_251856_dh00' in line:
        r=json.loads(line); n+=1
        row=r.get('row',r)
        print('third control row keys',sorted(row)[:40])
        print('  qid',row.get('qid'),'r1_source' in row,'s1_source.name',(row.get('s1_source') or {}).get('name'),'dataset',row.get('dataset'),'question_type',row.get('question_type'))
print('third control matches',n)
PY

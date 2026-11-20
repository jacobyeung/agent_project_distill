X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/173881; U=$X/u; TZ=UTC date +%TZ; df -h /project/community | tail -1

sha256sum $O/rd0/rdiff_summary.json

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
na=json.load(gzip.open(O+'/na.json.gz'))
rows=na['rows']; print('na keys',sorted(na)[:20],'rows',len(rows),'row keys',sorted(rows[0]))
c=collections.Counter(); L=collections.Counter(); src=collections.Counter()
for r in rows:
    s=r['key'][0]+'/'+r['key'][1]; inm=s in M; lists=[h[:8] for h in (r.get('removal_list_sha256s') or [])]
    c['scene_in_merged']+=inm; c['scene_in_P_dev']+= s in Dn
    if not inm:
        c['not_in_merged']+=1; c['not_in_merged_on_6add0ad5']+= '6add0ad5' in lists
        for h in lists: L[h]+=1
    else: c['in_merged_also_listed']+=bool(lists)
    src[(r.get('source') or r.get('s1_source') or '?', 'scene' if inm else 'list')]+=1
print(dict(c)); print('lists of na rows not in merged',dict(L)); print('by source',dict(src))
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

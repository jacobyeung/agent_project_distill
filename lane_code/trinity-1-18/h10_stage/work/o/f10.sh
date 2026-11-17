W=/project/community/jjyeung/okh7/e6fc152498; sha256sum $W/callcount.json $W/callcount.py | cut -c1-16
python3 - <<'P'
import json,collections
d=json.load(open('/project/community/jjyeung/okh7/e6fc152498/callcount.json'))
for q in ('object_abs_distance','room_size_estimation'):
    tot=collections.Counter(); ns=collections.Counter(); mx=0
    for f,v in d.items():
        if q in v['types']:
            for k,n in v['dist'].items():
                a,b,c=k.split('|')
                if a==q: tot[(f[:8],int(b),int(c))]+=n
            for k,n in v['not_seen'].items():
                if k.startswith(q+'|'): ns[(f[:8],k.split('|')[1])]+=n
            mx=max(mx,v['max_ground_gap'].get(q,0))
    print(q,'MAX',mx); print(' dist(file,ncalls,ground+gap):',sorted(tot.items()))
    print(' not_seen:',sorted(ns.items()))
    for f,v in d.items():
        if q in v.get('not_seen_example',{}): print(' NS-EX',f[:8],json.dumps(v['not_seen_example'][q])[:900]); break
P

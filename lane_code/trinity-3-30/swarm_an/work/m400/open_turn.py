import json; from collections import Counter
D=json.load(open('/tmp/san_dircls.json'))
for st in ('100','200','400'):
    v=[x for x in D['R1|%s|R0-dev'%st] if x['away']]
    c=Counter((x['open'],x['turn']) for x in v); w=Counter((x['open'],x['turn']) for x in v if not x['right'])
    print('R0-dev away',st,'; '.join('%s/%s n%d wr%d'%(a,b,n,w[(a,b)]) for (a,b),n in sorted(c.items())))
    v=[x for x in D['R1|%s|R0-dev'%st] if not x['away']]
    print('R0-dev toward',st,dict(Counter((x['open'],x['turn']) for x in v)))
    for s in ('dev-S1','forward'):
        if st=='100' and s=='forward': continue
        print(' ',s,st,dict(Counter((x['open'],x['turn']) for x in D['R1|%s|%s'%(st,s)])))
# transitions on toward hard, direct + forward: 544 -> 400
for s in ('forward','dev-S1','R0-dev'):
    A={x['id']:x for x in D['S1|544|'+s]}; B={x['id']:x for x in D['R1|200|'+s]}; C={x['id']:x for x in D['R1|400|'+s]}
    for ty in ('easy','medium','hard'):
        ks=[k for k in C if C[k]['type']==ty and not C[k]['away']]
        t=Counter(('R' if A[k]['right'] else 'W')+('R' if B[k]['right'] else 'W')+('R' if C[k]['right'] else 'W') for k in ks)
        lost=[k for k in ks if A[k]['right'] and not C[k]['right']]
        fbl=Counter((C[k]['truth'],C[k]['final']) for k in lost)
        print('%s toward %s 544/200/400 patterns %s; lost since 544 %d: %s'%(s,ty,dict(t),len(lost),dict(fbl.most_common(6))))

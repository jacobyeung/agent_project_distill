import json, math, collections, random, statistics as st
from load import mra
rows=json.load(open('size_rows_544_m200.json'))
TO_CM={'cm':1.0,'m':100.0,'in':2.54,'ft':30.48}
def slip(pred,gt,u, lo=math.log(1.6), hi=math.log(1.35)):
    gcm=gt*TO_CM[u]
    e_own=abs(math.log(pred/gt))
    cands=[(abs(math.log(pred*TO_CM[v]/gcm)),v) for v in TO_CM if v!=u]
    e,v=min(cands)
    if e_own>lo and e<hi and e<e_own: return v, pred*TO_CM[v]/TO_CM[u]
    return None, pred
out={}
for lab in 'ab':
    S=collections.Counter(); fixed=[]
    for r in rows:
        v,p2=slip(r['p'+lab],r['g'],r['u'])
        if v: S[(r['u'],v)]+=1
        r['slip'+lab]=v; r['fix'+lab]=mra(p2,r['g'])
    out[lab]=S
    print('export','544' if lab=='a' else 'm200','unit slips',sum(S.values()),dict(S))
n=len(rows)
for lab in 'ab':
    print('  MRA raw %.2f  with slips reinterpreted %.2f'%(100*sum(r['s'+lab] for r in rows)/n,100*sum(r['fix'+lab] for r in rows)/n))
# paired room bootstrap
def boot(diffs_by_room, B=10000, seed=20261115):
    rnd=random.Random(seed); rooms=list(diffs_by_room); vals=[]
    for _ in range(B):
        s=0; c=0
        for _ in rooms:
            d=diffs_by_room[rnd.choice(rooms)]; s+=sum(d); c+=len(d)
        vals.append(100*s/c)
    vals.sort(); return vals[int(0.025*B)], vals[int(0.975*B)-1]
def paired(fa,fb,R):
    by=collections.defaultdict(list)
    for r in R: by[r['room']].append(fb(r)-fa(r))
    d=100*sum(sum(v) for v in by.values())/sum(len(v) for v in by.values())
    lo,hi=boot(by); return d,lo,hi,len(R),len(by)
print('paired m200-544 raw: %+.2f [%.2f, %.2f] n=%d rooms=%d'%paired(lambda r:r['sa'],lambda r:r['sb'],rows))
print('paired m200-544 both slip-fixed: %+.2f [%.2f, %.2f] n=%d rooms=%d'%paired(lambda r:r['fixa'],lambda r:r['fixb'],rows))
print('paired m200-544 on items where neither export slips: %+.2f [%.2f, %.2f] n=%d rooms=%d'%paired(lambda r:r['sa'],lambda r:r['sb'],[r for r in rows if not r['slipa'] and not r['slipb']]))
for u in ['cm','m','in','ft']:
    R=[r for r in rows if r['u']==u]
    print(u,'raw %+.2f [%.2f, %.2f] n=%d rooms=%d'%paired(lambda r:r['sa'],lambda r:r['sb'],R), '| slip-fixed %+.2f [%.2f, %.2f]'%paired(lambda r:r['fixa'],lambda r:r['fixb'],R)[:3], '| slips 544 %d m200 %d'%(sum(1 for r in R if r['slipa']),sum(1 for r in R if r['slipb'])))
json.dump(rows,open('size_rows_544_m200_slip.json','w'))
# slips list for m200
for r in rows:
    if r['slipb'] or r['slipa']: print('   %-14s asked %-2s gt %7.2f | 544 %7.2f slip=%s s=%.1f | m200 %7.2f slip=%s s=%.1f'%(r['id'],r['u'],r['g'],r['pa'],r['slipa'],r['sa'],r['pb'],r['slipb'],r['sb']))

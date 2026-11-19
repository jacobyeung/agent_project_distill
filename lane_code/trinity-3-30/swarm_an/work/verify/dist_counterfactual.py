"""Routed distance (150 dev-S1 items): price of each fix by counterfactual on the scored truth."""
import sys,re,json; sys.path.insert(0,'/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
def mra(p,g):
    if p is None: return 0.0
    g=float(g); e=abs(p-g)/abs(g); return sum(e<=1-t/100+1e-12 for t in range(50,100,5))/10
fac={'m':1.0,'cm':100.0,'ft':1/.3048,'in':1/.0254}
def unit(q):
    q=q.lower()
    if re.search(r'centimet|\bcm\b',q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b',q): return 'ft'
    if re.search(r'\binch',q): return 'in'
    return 'm'
def gap(r):
    g=[re.search(r'distance ([\d.]+) m',c['response'] or '') for c in r['calls'] if c['family']=='gap']; g=[float(x.group(1)) for x in g if x]
    return g[-1] if g else None
new={r['id']:r for r in K.routed(200,types=['object_abs_distance'])}; old={r['id']:r for r in K.routed(544,types=['object_abs_distance'])}
N=len(new); act=sum(r['score'] for r in new.values())/N*100; act544=sum(r['score'] for r in old.values())/N*100
tot={k:0.0 for k in ('all_call_faithful','only_nocall_fixed','only_conversion_fixed','faithful544','perfect_gap_where_available')}
byu={}
for i,r in new.items():
    u=unit(r['question']); f=fac[u]; g2=gap(r); g5=gap(old[i]); t=r['gt']
    a=mra(g2*f,t) if g2 is not None else (mra(g5*f,t) if g5 is not None else r['score'])
    tot['all_call_faithful']+=a
    tot['only_nocall_fixed']+= r['score'] if r['ncalls']>0 else (mra(g5*f,t) if g5 is not None else r['score'])
    tot['only_conversion_fixed']+= (mra(g2*f,t) if g2 is not None else r['score']) if r['ncalls']>0 else r['score']
    tot['faithful544']+= mra(g5*f,t) if g5 is not None else old[i]['score']
    tot['perfect_gap_where_available']+= 1.0 if (g2 is not None or g5 is not None) else r['score']
    x=byu.setdefault(u,[0,0.0,0.0,0]); x[0]+=1; x[1]+=r['score']; x[2]+=a; x[3]+=r['ncalls']>0
out=dict(items=N,actual_544=round(act544,2),actual_200=round(act,2),**{k:round(100*v/N,2) for k,v in tot.items()},by_unit={u:dict(n=v[0],calls_200=v[3],actual_200=round(100*v[1]/v[0],1),all_call_faithful=round(100*v[2]/v[0],1)) for u,v in byu.items()})
print(json.dumps(out,indent=1)); json.dump(out,open('DIST_COUNTERFACTUAL.json','w'),indent=1)

"""Select source-grounded pairs under explicit category and pair-name caps."""
from common import *
from wordings import BUCKET_QUOTAS
import collections, numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

def solve(pairs,sources,roommap,cap,seed=19,limit=120):
 npairs=len(pairs);bucket_vars={b:npairs+j for j,b in enumerate(BUCKET_QUOTAS)};n=npairs+len(bucket_vars);groups=collections.defaultdict(list); cats=collections.defaultdict(list);names=collections.defaultdict(list);physical=collections.defaultdict(list)
 for i,p in enumerate(pairs):
  s=sources[p['source_qid']]
  for key in [('source',s['qid']),('scene',s['provenance']['canonical']),('bucket',p['bucket'])]:groups[key].append(i)
  if p['na']!=p['nb']:
   winner=p['a'] if p['na']>p['nb'] else p['b']
   for a in (p['a'],p['b']):cats[a].append((i,a==winner))
  else:winner='tie'
  names[tuple(sorted((p['a'],p['b'])))].append((i,winner))
  physical[(roommap[s['provenance']['canonical']],*sorted((p['a'],p['b'])))].append((i,winner))
 rr=[];cc=[];vv=[];lo=[];hi=[]
 def cons(items,l=-np.inf,h=np.inf):
  j=len(lo);lo.append(l);hi.append(h)
  for i,v in items:
   if v:rr.append(j);cc.append(i);vv.append(v)
 for (kind,key),ids in groups.items():
  if kind=='source':cons(((i,1) for i in ids),h=8)
  elif kind=='scene':cons(((i,1) for i in ids),h=24)
  elif key=='tie':cons(((i,1) for i in ids),400,400)
  else:cons([(i,1) for i in ids]+[(bucket_vars[key],-40)],0,0)
 for a,items in cats.items():
  for direction in [True,False]:cons(((i,float(win==direction)-cap) for i,win in items),h=0)
 for key,items in names.items():
  unequal=[(i,w) for i,w in items if w!='tie']
  for a in key:cons(((i,float(w==a)-cap) for i,w in unequal),h=0)
  for a in (*key,'tie'):cons(((i,float(w==a)-cap) for i,w in items),h=0)
 extra_vars=0
 for key,items in physical.items():
  labels=sorted({w for i,w in items})
  if len(labels)<2:continue
  zvars={label:n+j for j,label in enumerate(labels)};n+=len(labels);extra_vars+=len(labels)
  cons([(j,1) for j in zvars.values()],h=1)
  for i,w in items:cons([(i,1),(zvars[w],-4)],h=0)
 # Prioritize direction-matched instances; maximize surviving rows first.
 matched={k for k,items in names.items() if len({w for i,w in items if w!='tie'})==2}
 rng=np.random.default_rng(seed)
 obj=np.array([-1.-(1e-5 if tuple(sorted((p['a'],p['b']))) in matched else 0)-rng.uniform(0,1e-7) for p in pairs]+[0.]*(len(bucket_vars)+extra_vars))
 matrix=coo_matrix((vv,(rr,cc)),shape=(len(lo),n)).tocsc()
 result=milp(obj,integrality=np.ones(n),bounds=Bounds(np.array([0]*npairs+[1]*len(bucket_vars)+[0]*extra_vars),np.array([1 if p['bucket']=='tie' else 4 for p in pairs]+list(BUCKET_QUOTAS.values())+[1]*extra_vars)),constraints=LinearConstraint(matrix,lo,hi),options={'time_limit':limit,'mip_rel_gap':.001,'threads':8})
 if result.x is None:return None,dict(status='NO_FEASIBLE_INCUMBENT',message=result.message)
 x=np.rint(result.x).astype(int);v=matrix@x
 assert np.all(v>=np.array(lo)-1e-6) and np.all(v<=np.array(hi)+1e-6)
 selected=[dict(p,uses=int(k)) for p,k in zip(pairs,x) if k]
 return selected,dict(status='FEASIBLE',rows=int(sum(x[:npairs])),solver_message=result.message,mip_gap=result.mip_gap,dual_bound=result.mip_dual_bound,category_cap=cap,pair_direction_cap=cap,per_template_bucket_quota={b:int(x[j]) for b,j in bucket_vars.items()},per_bucket=dict(collections.Counter({b:sum(int(x[i]) for i in ids) for (kind,b),ids in groups.items() if kind=='bucket'})))

def main():
 census=load(BASE/'in/CENSUS.json');sources={r['qid']:r for r in rows(SRC)}
 old=list(rows(ROOT.parent/'relcnt/out/relative_count.jsonl'));roommap={r['provenance']['canonical']:r['provenance']['relative_count']['room'] for r in old}
 for cap in [.65,.60]:
  selected,info=solve(census['pairs'],sources,roommap,cap)
  pin(ROOT/'code/solve.py');pin(ROOT/'code/common.py');pin(ROOT/'code/wordings.py')
  dump(ROOT/f'out/SELECTION_{int(cap*100)}.json',dict(input_sha256=dict(PINS),command='bash code/run.sh code/solve.py',summary=info,selected=selected))
  print(info,flush=True)
 status('Source-grounded selections at the 0.65 and 0.60 caps are recorded with category and pair-direction constraints. All selected counts come from the eligible census. Final template allocation, measured leave-one-out priors, validators, and packet review remain pending.')
if __name__=='__main__':main()

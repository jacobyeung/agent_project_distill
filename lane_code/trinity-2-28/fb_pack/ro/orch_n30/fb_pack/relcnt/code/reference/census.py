from common import *
import collections,itertools,numpy as np
from concurrent.futures import ProcessPoolExecutor

def raster_facts(path):
 p=Path(path);h=sha(p)
 with np.load(p,allow_pickle=False) as z:
  a=z['inst'];ids=list(map(int,z['ids']));labels=list(map(norm,z['labels']));den=a.shape[1]*a.shape[2]
  maxid=max(ids+ [int(a.max())]);counts=np.stack([np.bincount(f.ravel()+1,minlength=maxid+2)[1:] for f in a])
  valid=(z['valid'].astype(bool)&(z['depth']>0).any(axis=(1,2))).tolist() if 'valid' in z else [True]*len(a)
  by=collections.defaultdict(list)
  for i,l in zip(ids,labels):by[l].append(i)
  cats={}
  for cat,ii in by.items():
   seen={i:np.flatnonzero(counts[:,i]/den>=.002).tolist() for i in ii}
   if all(seen[i] and all(valid[:seen[i][0]]) for i in ii):cats[cat]={'n':len(ii),'ids':ii,'first':[seen[i][0]+1 for i in ii]}
  return p.name,{'path':str(p),'sha256':h,'frame_indices':z['frame_indices'].tolist(),'categories':cats,'all_labels':dict(by)}

def main():
 rooms,allowed,_=setup_rooms();rows=[json.loads(l) for l in SRC.open()];pin(SRC)
 idx={p.name:p for p in (ROOT/'in/b12gt/work/rasters').rglob('*.npz')}
 # Only byte-identical b12 rasters qualify; unrelated raw raster variants are not substituted.
 need={};c=collections.Counter();available=[]
 for r in rows:
  st=allowed(r)
  if st!='ok':c['room_'+st]+=1;continue
  name=r['provenance']['raster']
  if name not in idx:c['MISSING_raster']+=1;continue
  need[name]=idx[name];available.append(r)
 facts={}
 with ProcessPoolExecutor(max_workers=8) as pool:
  for name,value in pool.map(raster_facts,need.values()):facts[name]=value
 pairs=[];bins=collections.Counter();unique=set()
 for r in available:
  f=facts[r['provenance']['raster']]
  if f['sha256']!=r['provenance']['raster_sha256']:c['raster_sha_mismatch']+=1;continue
  assert f['frame_indices']==r['student_input']['frame_indices']
  cats=r['provenance']['total_categories']
  for cat in cats:
   v=f['categories'].get(cat['name']);assert v and sorted(v['ids'])==sorted(cat['ids'])
  assert sum(len(cat['ids']) for cat in cats)==int(r['answer'])
  for a,b in itertools.combinations(cats,2):
   n,m=len(a['ids']),len(b['ids']);key=(r['provenance']['canonical'],*sorted([a['name'],b['name']]))
   if key in unique:continue
   unique.add(key);bucket='tie' if n==m else str(min(max(n,m),10))
   bins[bucket]+=1;pairs.append(dict(source_qid=r['qid'],a=a['name'],b=b['name'],na=n,nb=m,bucket=bucket))
  c['eligible_sources']+=1
 out=dict(input_sha256=PINS,facts=facts,pairs=pairs,counts=dict(c),buckets=dict(bins))
 dump(ROOT/'in/CENSUS.json',out);print(json.dumps({'counts':dict(c),'buckets':dict(bins),'rasters':len(facts)}))
 status('The w19 sealed tree, scorer, procedure source, and physical-room exclusions are identified. The local GT census is recorded in in/CENSUS.json; generation and independent validation remain pending.')
if __name__=='__main__':main()

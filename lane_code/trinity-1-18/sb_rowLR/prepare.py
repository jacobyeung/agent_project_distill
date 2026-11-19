import ast,copy,itertools,json,collections,hashlib
from pathlib import Path
import numpy as np
from census import W,BASE,TREE,reg,INPUTS,rules,status,dump
from student_pilot import r2_adapters,r2_contract,trace_grammar
# These helpers are the exact codeF/room_v4 implementations, without its path-bound common import.
p=reg('/scratch/jjyeung/n30_mirror/rows_r1/work/codeF/build_room.py');tree=ast.parse(p.read_text());ns={'re':__import__('re'),'np':np}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in {'norm','stems','metadata'} or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BANNED' for t in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),ns)
norm,stems,BANNED=ns['norm'],ns['stems'],ns['BANNED']
def landmarks(z,up=2):
 shares=collections.defaultdict(dict)
 for f,frame in enumerate(z['inst'],1):
  ids,cts=np.unique(frame,return_counts=True)
  for iid,n in zip(ids,cts):
   if iid>=0 and n/frame.size>=.01:shares[int(iid)][f]=float(n/frame.size)
 labels=[norm(x) for x in z['labels']];freq=collections.Counter(labels);rank=sorted(range(len(labels)),key=lambda j:(-float(np.prod(np.sort(z['obb_lengths'][j])[-2:])),int(z['ids'][j])))
 selected=[];words=set()
 for j in rank:
  label=labels[j];ws=stems(label);iid=int(z['ids'][j])
  if not shares[iid] or freq[label]!=1 or label in BANNED or __import__('re').search(r'\d',label) or ws&words:continue
  best=min(shares[iid],key=lambda f:(-shares[iid][f],f))
  selected.append(dict(instance_id=iid,label=label,best_view=best,pixel_share=shares[iid][best],footprint=float(np.prod(np.sort(z['obb_lengths'][j])[-2:])),centroid=z['obb_centroid'][j].tolist()));words|=ws
  if len(selected)==3:break
 summary=dict(landmarks=selected,up_axis=up)
 if len(selected)<2:return summary
 hor=[j for j in range(3) if j!=up];coords=np.array([x['centroid'] for x in selected])[:,hor];pairs=list(itertools.combinations(range(len(selected)),2));a,c=max(pairs,key=lambda ij:float(np.linalg.norm(coords[ij[0]]-coords[ij[1]])));delta=coords[c]-coords[a];length=float(np.linalg.norm(delta))
 if length<=0:return summary
 rel=dict(pair=[a,c],horizontal_axes=hor,horizontal_centroids=coords.tolist(),segment_length=length,rule='farthest Euclidean pair; third projection in [0.25,0.75] and perpendicular distance < 0.35 * length')
 if len(selected)==3:
  b=next(j for j in range(3) if j not in [a,c]);t=float(np.dot(coords[b]-coords[a],delta)/np.dot(delta,delta));distance=float(np.linalg.norm(coords[b]-(coords[a]+t*delta)));rel.update(third=b,projection=t,perpendicular_distance=distance,decision='between' if .25<=t<=.75 and distance<.35*length else 'side')
 else:rel['decision']='pair_only'
 summary['relate']=rel;return summary

def main():
 c=json.load(open(W/'out/CENSUS.json'));INPUTS.update(c['input_sha256']);reg(W/'out/CENSUS.json');reg(W/'inputs/binding_sources.jsonl');reg(__file__)
 rs,extra=rules();bycan=collections.defaultdict(list)
 for line in open(W/'inputs/binding_sources.jsonl'):
  r=json.loads(line);can,_=rs.canonical(r);bycan[can.replace('scannetppv2/','scannetpp/')].append(r)
 out=[]
 for e in c['entries']:
  if e['exclusions'] or not e.get('measurement'):continue
  x=copy.deepcopy(e);good=[];errors=[]
  for src in bycan[e['canonical']]:
   try:
    normalized=r2_adapters.normalize(src);r2_contract.validate(normalized,'vqa');good.append(src)
   except Exception as ex:errors.append(dict(qid=src['qid'],error=str(ex)))
  x['source_validator_rejections']=errors
  if good:x['source']=min(good,key=lambda r:hashlib.sha256(r['qid'].encode()).hexdigest())
  with np.load(e['path']) as z:
   x['trace']=landmarks(z);ev=[]
   for j,label in enumerate(z['labels']):
    if norm(label)=='floor':
     axes=z['obb_axes'][j].reshape(3,3);normal=axes[int(np.argmin(z['obb_lengths'][j]))];up=int(np.argmax(np.abs(normal)));ev.append(dict(up_axis=up,camera_height=float(np.median(z['c2w'][:,up,3])-z['obb_centroid'][j,up])))
   x['floor_axis_evidence']=ev
  x['buildable']=bool(good) and 'relate' in x['trace'] and all(ev['up_axis']==2 and ev['camera_height']>0 for ev in x['floor_axis_evidence'])
  out.append(x)
 dump(W/'out/PREPARED.json',dict(entries=out,counts=dict(collections.Counter(x['canonical'].split('/')[0]+'|'+x['band'] for x in out if x['buildable']))))
 print('BUILDABLE',collections.Counter(x['canonical'].split('/')[0]+'|'+x['band'] for x in out if x['buildable']));print('large refused',[(x['canonical'],x['source_validator_rejections'],len(x['trace']['landmarks']),x['floor_axis_evidence']) for x in out if x['measurement']['area_m2']>=40 and not x['buildable']])
if __name__=='__main__':main()

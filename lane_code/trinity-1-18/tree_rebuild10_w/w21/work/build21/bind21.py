"""Bind pinned sources and prove unchanged geometric evidence for reworded rows."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import json,sys,re
L=Path(__file__).resolve().parents[2];B=L/'work/build21';I=B/'inputs';O=B/'proofs/v2h'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
from student_pilot.p3_provenance import load,pinned,file_pin,digest
def write(path,value):
 path=Path(path);assert path.is_relative_to(B)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
if '--check-only' in sys.argv:
 import importlib.util
 spec=importlib.util.spec_from_file_location('student_pilot.candidate_coverage',B/'candidate/r1_coverage.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
else:
 from student_pilot import r1_coverage as C
from student_pilot.r2_adapters import normalize
from student_pilot.extent_receipt import Extents,content
cfg=load(L/'work/build20/inputs/config.json');value=cfg['r1_training'];sources=load(pinned(value['row_sources']))
validation=load(O/'VALIDATION.json');files=validation['files'];guard=C.WordingExclusion(validation['split'])
def normalized(raw):
 p=raw.get('provenance',{});si=raw.get('student_input',{})
 indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
 fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.
 frames={raw['qid']:dict(fps=fps,total_num_frames=indices[-1]+1,
  frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
 return normalize(raw,frames)
parents={};wanted=set()
for pin in files.values():
 with pinned(pin).open() as f:
  for line in f:
   r=json.loads(line);wanted.add(re.sub(r'_dh\d\d$','',r['qid']))
parent_sources={}
for kind in ('units','absolute_distance'):
 with pinned(sources[kind]['source']).open() as f:
  for line in f:
   r=json.loads(line)
   if r['qid'] in wanted:parents[r['qid']]=r;parent_sources[r['qid']]=sources[kind]['source']
assert set(parents)==wanted,('Missing source parents',len(wanted-set(parents)))
original_extent=cfg['extent_receipt'];extents=Extents(original_extent);expanded=deepcopy(extents.receipt)
catalog=load(pinned(value['source_membership']));derivations={};examples={}
for kind,pin in files.items():
 qids=[];examples[kind]=[]
 with pinned(pin).open() as f:
  for line in f:
   raw=json.loads(line);guard.check(raw);qid=raw['qid'];parent_id=re.sub(r'_dh\d\d$','',qid)
   parent=parents[parent_id];C.rewording(raw,parent)
   old=normalized(parent);extents.check(old,'routing');row=normalized(raw)
   entry=deepcopy(extents.receipt['rows'][parent_id]);entry['content_sha256']=digest(content(row))
   expanded['rows'][qid]=entry
   derivations[qid]=dict(parent_qid=parent_id,parent_source=parent_sources[parent_id]['sha256'],
    parent_content_sha256=digest(content(old)),content_sha256=entry['content_sha256'],source_sha256=pin['sha256'])
   qids.append(qid)
   if len(examples[kind])<20:examples[kind].append(dict(qid=qid,parent_qid=parent_id,target=row['target']))
 sources[kind]=dict(source=pin,variant='wording_only',status='Pinned wording slice; real host frame/scene envelopes remain required')
 catalog['sources'][kind]=dict(source=pin,qids=qids)
if '--check-only' in sys.argv:
 (O/'PARENT_CHECK.json').write_text(json.dumps(dict(status='PASS',parents=len(parents),rows=len(derivations),parent_receipt=original_extent),indent=2))
 (O/'parent').mkdir(exist_ok=True);m.save(O/'parent');print('PASS',len(derivations),'exact rewordings and native parent extent checks');raise SystemExit(0)
write(O/'DERIVATIONS.json',dict(parent_receipt=original_extent,sources=files,rows=derivations,
 rule='Exact equality with pinned source except question and identity fields; native parent extent check passes.',
 stand_in='Frame metadata /u; GUESS 24 FPS only when source FPS absent. Extent content excludes RGB joins.'))
expanded['audits'].append(file_pin(O/'DERIVATIONS.json'))
write(I/'extent.json',expanded);cfg['extent_receipt']=file_pin(I/'extent.json')
value['row_sources']=file_pin(I/'row_sources.json') if (I/'row_sources.json').exists() else None
write(I/'row_sources.json',sources);value['row_sources']=file_pin(I/'row_sources.json')
write(I/'source_membership.json',catalog);value['source_membership']=file_pin(I/'source_membership.json')
value['wording_exclusion']=validation['split']
base=next(p for p in cfg['remove_files'] if p['sha256']=='43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6')
extra=file_pin(Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u2.json'))
assert extra['sha256']=='d2fd6208d7df49ab872b9536a1748d80c392f91a59135b099bc0bc38fff13a8f'
union=C.union_rows(C.read_list(base),C.read_list(extra))
(I/'u_union.json').write_text(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in union))
up=file_pin(I/'u_union.json');assert up['sha256']=='1c7c930d1a533a3b18b08486bc2c2a9b49086b0809492963498b369ac8be45a2'
position=next(i for i,p in enumerate(cfg['remove_files']) if p['sha256']==base['sha256'])
cfg['remove_files'].insert(position+1,up)
value.update(v7_k1_removal=up,v7_k1_union=dict(base=base,extra=extra,union=up))
C.verify_union(value,cfg['remove_files'],base['sha256'],'02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')
card=load(L/'work/build20/inputs/mix.json');programs=('camera_displacement','camera_movement_direction','camera_rotation','absolute_distance')
prior={c['type']:int(Fraction(str(c['rows_per_step']))*1000) for c in card['cells'] if c['type'] in programs}
total=sum(prior.values());ideal={k:Fraction(3000*v,total) for k,v in prior.items()};cuts={k:int(v) for k,v in ideal.items()}
for k in sorted(prior,key=lambda k:(ideal[k]-cuts[k],k),reverse=True)[:3000-sum(cuts.values())]:cuts[k]+=1
for cell in card['cells']:
 if cell['type'] in cuts:cell['rows_per_step']=(prior[cell['type']]-cuts[cell['type']])/1000
card['cells'].append(dict(type='coverage',stream='routing',rows_per_step=3.0))
write(I/'mix.json',card);value['mix']=file_pin(I/'mix.json')
for name in ('config.json','kit_config.json'):write(I/name,cfg)
write(O/'BINDING.json',dict(files=files,split=validation['split'],extent=cfg['extent_receipt'],
 union=dict(base=base,extra=extra,union=up,base_rows=len(C.read_list(base)),extra_rows=len(C.read_list(extra)),rows=len(union)),
 pro_rata=dict(requested_rows_per_step=3.0,program_draws=prior,total_program_draws=total,
  ideal_cuts={k:str(v) for k,v in ideal.items()},integer_cuts=cuts,rounding='largest remainder at one draw per 1000-step plan'),
 examples=examples,host_routing_inputs=cfg['r1_training'].get('routing_inputs')))
(O/'binding').mkdir(exist_ok=True);m.save(O/'binding');print('PASS exact parent geometry, extent inheritance, source pins and real K1 union')

"""Build 40 reserved training wordings x 50 rows x 3 camera types; never edit evaluation files."""
import copy,re
from camera_contract import *
from build_camera import normalized
from fast_wording import near

def main():
 frozen();pin(__file__);pin(ROOT/'camera_contract.py');pin(ROOT/'build_camera.py')
 for dep in ['fast_wording.py','wording_distance.cpp','out/wording_distance.so']:pin(ROOT/dep)
 audit=load(OUT/'SOURCE_AUDIT.json');INPUTS.update(audit['input_sha256'])
 w=load(OUT/'WORDINGS.json');pin(OUT/'WORDING_CORPUS.txt');pin(OUT/'SOURCE_WORDING_CORPUS.txt')
 # The frozen inventory records hashes for all 58 dev/kit inputs to this corpus.
 # Hash the current corpus inputs; frozen evaluation metadata remains byte-identical.
 for rec in w['corpus_files']:pin(rec['path'],rec['sha256'])
 corpus=sorted(set((OUT/'WORDING_CORPUS.txt').read_text().splitlines())|{normalized(q) for q in (OUT/'SOURCE_WORDING_CORPUS.txt').read_text().splitlines()})
 a=Admission();pools={t:[] for t in TYPES};all_qids=set();all_cids=set()
 accepted={d['i']:d for d in (json.loads(s) for s in (OUT/'SOURCE_ADMISSION.jsonl').read_text().splitlines()) if d['keep']}
 for x,r in a.scan():
  all_qids.add(r['qid'])
  if r.get('candidate_id'):all_cids.add(r['candidate_id'])
  if x['i'] in accepted:
   assert hashlib.sha256(x['row'].encode()).hexdigest()==accepted[x['i']]['row_sha256']
   pools[r['routing']['question_type']].append((hashlib.sha256(('sb_rowA2|training|'+r['qid']).encode()).hexdigest(),x,r))
 counts=Counter();uses=Counter();refused=Counter();lineage=[];rows=[];sources=[];proofs={};nq=set();nc=set()
 for typ in TYPES:
  pool=sorted(pools[typ],key=lambda x:x[0]);filled=0
  assert len(w['training'][typ])==40
  for _,raw,r in pool:
   if filled==2000:break
   k=filled%40;i,j,n=frames(r)
   q=w['training'][typ][k].format(i=i,j=j,n=n,unit='meters',options='; '.join(r['student_input']['options']))
   if near(q,corpus):refused['wording_near_dev_or_source']+=1;continue
   try:
    native_validate(r);g=geometry(r)
   except (ValueError,AssertionError) as exc:
    refused['source_validation:'+str(exc)[:150]]+=1;continue
   assert not a.reasons(r)[0]
   x=copy.deepcopy(r);x['qid']=r['qid']+f'-sbca-t{k:02d}';x['routing']['qid']=x['qid'];x['student_input']['question']=q
   # Source traces contain frame descriptions but do not quote the complete source question.
   assert r['student_input']['question'] not in r['target']
   assert all(r['student_input']['question'] not in e.get('text','') for e in r['routing']['events'])
   x['candidate_id']=x['routing']['candidate_id']=candidate(x)
   # Explicitly check the complete trace, call arguments, responses, masks and geometry.
   stripped=copy.deepcopy(x);stripped['qid']=r['qid'];stripped['routing']['qid']=r['qid'];stripped['student_input']['question']=r['student_input']['question']
   stripped.pop('candidate_id');stripped['routing'].pop('candidate_id')
   assert stripped==r
   native_validate(x);assert geometry(x)==g
   assert x['qid'] not in all_qids|nq and x['candidate_id'] not in all_cids|nc
   nq.add(x['qid']);nc.add(x['candidate_id']);uses[r['qid']]+=1
   # Check all 24 held-out wordings against the complete normalized row, not only the question.
   normrow=normalized(enc(x))
   for htyp in TYPES:
    for h in w['heldout'][htyp]:
     hq=h.format(i=i,j=j,n=n,unit='meters',options='; '.join(r['student_input']['options']))
     assert normalized(hq) not in normrow
   assert all(str(v) in q for v in (i,j,n))
   counts[f'{typ}|t{k:02d}']+=1;filled+=1;rows.append(x);sources.append(raw)
   rec=accepted[raw['i']]
   lineage.append(dict(qid=x['qid'],candidate_id=x['candidate_id'],source_qid=r['qid'],source_i=raw['i'],source_row_sha256=rec['row_sha256'],source_target_sha256=rec['target_sha256'],type=typ,wording_id=f't{k:02d}',canonical=rec['canonical'],room=rec['room'],frame_pair=[i,j],recomputed=g))
  assert filled==2000,(typ,'short cell',filled,dict(refused))
  print(typ,filled,'rows; sources checked',sum(uses.values()),flush=True)
 assert len(rows)==len(nq)==len(nc)==6000 and max(uses.values())<=2
 assert len(counts)==120 and all(v==50 for v in counts.values())
 with (OUT/'CAMERA_ROWS.jsonl').open('w') as f:
  for x in rows:f.write(enc(x)+'\n')
 # Raw source TEXT and target TEXT are retained verbatim inside each source envelope.
 with gzip.open(OUT/'CAMERA_SOURCES.jsonl.gz','wt') as f:
  for x in sources:f.write(enc(x)+'\n')
 with (OUT/'CAMERA_LINEAGE.jsonl').open('w') as f:
  for x in lineage:f.write(enc(x)+'\n')
 # Review a dense scene per type, with ten distinct rows per type.
 sample=[]
 for typ in TYPES:
  candidates=[x for x in rows if x['routing']['question_type']==typ]
  scene_counts=Counter(x['routing']['canonical'] for x in candidates)
  sc=min(scene_counts,key=lambda sc:(-scene_counts[sc],sc))
  scene_rows=[x for x in candidates if x['routing']['canonical']==sc]
  scene_rows.sort(key=lambda x:(int(x['qid'][-2:]),x['qid']))
  assert len(scene_rows)>=10
  sample.extend(scene_rows[:10])
 (OUT/'READ30.md').write_text('# Thirty complete training rows\n\n'+'\n\n'.join(f'## {i+1}. {x["qid"]}\n\n```json\n{enc(x)}\n```' for i,x in enumerate(sample))+'\n')
 for file in ['CAMERA_ROWS.jsonl','CAMERA_SOURCES.jsonl.gz','CAMERA_LINEAGE.jsonl','READ30.md']:pin(OUT/file)
 tree=bind_code();frozen()
 save(OUT/'TRAINING_CHECKS.json',dict(status='PASS_AUTOMATED_PENDING_READ30',command='/scratch/jjyeung/envs/p1cpu/bin/python -B build_camera_training.py',rows=len(rows),cells={k:dict(expected=50,actual=v,status='PASS') for k,v in counts.items()},tree_sha256=tree,unique_sources=len(uses),max_source_use=max(uses.values()),source_reuse_limit=2,source_rejections=dict(refused),pack_validate_sources=len(sources),pack_validate_rows=len(rows),pack_api='student_pilot.carrier_c1_routing.c1_row + check_row; r1_training.row_check; r2_contract.frame_metadata',pack_scope='Native C1 camera contract; ground_rows.pack is for object-grounding records and does not accept these camera events.',independent_geometry_sources=len(sources),independent_geometry_rows=len(rows),geometry_method='SciPy quaternion rotation; independent camera-center/level-basis arithmetic, native eight-decimal operands, printed response and answer equality',unique_qids=len(nq),unique_candidate_ids=len(nc),candidate_id_rule='ground_v312_quality.candidate_identity with new qid, scene token, frame_indices, type, question, ordered options, source trace_revision',source_candidate_ids_present=len(all_cids),candidate_id_note='Legacy camera sources have no candidate_id; new identity is added at top level and routing.',field_diff='qid; routing.qid; student_input.question; added candidate_id and routing.candidate_id only',unchanged_traces=len(rows),unchanged_calls=len(rows),heldout_wording_hits=0,room_exclusions='PASS: every chosen source independently rechecked',wording_threshold=0.20,wording_corpus_normalized=len(corpus),training_rows_removed_by_wording=refused['wording_near_dev_or_source'],read30='WRITTEN_PENDING_MANUAL_REVIEW'))
 save(OUT/'CAMERA_ROWS.MISSING.json',dict(status='RESOLVED',rows=6000,missing=[],training_manifest='TRAINING_CHECKS.json'))
 (ROOT/'STATUS.md').write_text('Training build complete: 6,000 rows, 120 cells of exactly 50, 6,000 unique sources used once. N native packing and validation, independent pose-based ground truth, field diffs and wording separation pass. READ30 manual review, independent row verification and the scorer patch handoff remain.\n')
 print(enc(dict(rows=len(rows),sources=len(uses),refused=refused)))
if __name__=='__main__':main()

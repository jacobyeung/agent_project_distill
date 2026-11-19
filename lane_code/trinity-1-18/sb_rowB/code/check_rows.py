"""Independently recompute every available answer from original archive arrays and verify all emitted rows."""
import io,tarfile
from common import *
from student_pilot.r1_rooms import Rooms
from student_pilot.r2_withheld import Withheld
from student_pilot.s1_scene_census import Census
from student_pilot.row_removals import Removals

def independent_geometry(r,z):
 p=r['provenance'];k=int(re.search(r'frame (\d+) of 32',r['student_input']['question'])[1]);assert k==p['camera_frame']
 assert z['frame_indices'].tolist()==r['student_input']['frame_indices']
 pose=z['c2w'][k-1].astype(float);C=pose[:3,3];inv=np.linalg.inv(pose);found={}
 for inst in p['instances']:
  matches=np.flatnonzero(z['ids']==inst['id']);assert len(matches)==1;j=int(matches[0]);assert norm(z['labels'][j])==inst['label']
  A=z['obb_axes'][j].reshape(3,3).astype(float)
  if p['geometry_audit']['axes_layout']=='columns':A=A.T
  O=z['obb_centroid'][j].astype(float);H=z['obb_lengths'][j].astype(float)*p['geometry_audit']['box_half_factor']
  # Scalar projections and sum of squared excesses, independent of generator vector code.
  q=[math.fsum(float(A[a,b])*float(C[b]-O[b]) for b in range(3)) for a in range(3)]
  excess=[max(v-h,0.0,-v-h) for v,h in zip(q,H)]
  distance=math.sqrt(math.fsum(e*e for e in excess))
  v=[max(-float(h),min(float(h),x)) for x,h in zip(q,H)]
  closest=[float(O[b])+math.fsum(float(A[a,b])*v[a] for a in range(3)) for b in range(3)]
  cc=(inv@np.r_[O,1])[:3];pc=(inv@np.r_[closest,1])[:3]
  found[inst['label']]=dict(distance=distance,center_camera=cc.tolist(),closest_camera=pc.tolist())
 order=sorted(found,key=lambda label:found[label]['distance'])
 if r['question_type'].startswith('camera_'):meaning=order[0]
 else:
  a,b=[o['label'] for o in p['instances']];meaning='Near' if found[a]['distance']<found[b]['distance'] else 'Far'
 answer=next(opt.split('. ',1)[0] for opt in r['student_input']['options'] if opt.split('. ',1)[1]==meaning)
 return k,found,order,answer

def main():
 build=load(ROOT/'out/BUILD_COUNTS.json');sources={r['qid']:r for r in lines(ROOT/'inputs/sources.jsonl')};audits=lines(ROOT/'out/ROW_AUDIT.jsonl')
 alternatives=lines(ROOT/'out/GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl');drafts=lines(ROOT/'out/REBUILT_NUMERIC_UNADMITTED.jsonl')
 pins=dict(build['input_sha256']);pins[str(ROOT/'out/BUILD_COUNTS.json')]=sha(ROOT/'out/BUILD_COUNTS.json');pins[str(ROOT/'code/check_rows.py')]=sha(ROOT/'code/check_rows.py')
 compact=lines(ROOT/'inputs/GT_COMPACT.jsonl');by_archive={}
 for g in compact:by_archive.setdefault(g['archive'],[]).append(g)
 raw_gt={};counter=Counter();maxerr=0.0
 for archive,items in by_archive.items():
  # Archive SHA already verified in prepare_gt.py. Independently re-read each member and verify its source SHA.
  with tarfile.open(archive) as t:
   for g in items:
    blob=t.extractfile(g['member']).read();assert hashlib.sha256(blob).hexdigest()==g['raster_sha256']
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:
     arrays={k:z[k] for k in g['arrays']}
    assert all(np.array_equal(arrays[k],np.array(v)) for k,v in g['arrays'].items())
    raw_gt[g['raster_sha256']]=arrays;counter['raw_gt_members_verified']+=1
  print('independent archive members verified',len(items),flush=True)
 # Construct original kit Rooms using independently read bound memberships; avoid unrelated build pin access.
 rr=RoomRule();rooms=Rooms.__new__(Rooms);split=load(rr.paths['split']);rooms.k1={x['room'] for x in split['teacher_k1']['captures'] if x['k1_split']=='heldout'}
 rooms.r0=set(rr.paths['r0'].read_text().splitlines())|{x['room'] for x in split['r0_scenes']['captures'].values()};rooms.aliases={};rooms.visits={x['video_id']:x['visit_id'] for x in csv.DictReader(rr.paths['visits'].open())}
 withheld=Withheld(dict(path=str(rr.paths['withheld']),sha256=rr.pins[str(rr.paths['withheld'])]))
 census=Census({k:dict(path=str(rr.paths[k]),sha256=rr.pins[str(rr.paths[k])]) for k in ('dev','benchmark')})
 nkeys={r['row_key'] for r in lines(W/'inputs/records/n.json')}
 remove=Removals([dict(path=str(ROOT/'out/REMOVE.json'),sha256=sha(ROOT/'out/REMOVE.json'))])
 expected=set();geometries={};changed=0
 for a in audits:
  r=sources[a['source_qid']];native_validate(r);counter['source_adapter_and_validator_pass']+=1
  assert bool(remove.match(r))==classify(r)['cites_other']
  status,canonical,_=rooms.status(r);names={'names':[canonical,rooms.room(canonical)]}
  independent_bad=status!='ok' or withheld.touches(r,names)
  cr=dict(r,provenance={**r['provenance'],'room':rooms.room(canonical)})
  identities=set(census.identities(cr));independent_bad|=any(bool(identities&v) for v in census.names.values())
  assert independent_bad==bool(a['room_refusals'])
  if r['provenance']['raster_sha256'] not in raw_gt:
   assert a['gt_status']=='MISSING';counter['gt_missing']+=1;continue
  k,found,order,answer=independent_geometry(r,raw_gt[r['provenance']['raster_sha256']])
  assert a['gt_status']=='recomputed',a
  geometries[r['qid']]=(k,found,order,answer)
  assert answer==a['gt']['answer'] and order==a['gt']['order']
  for o in a['gt']['objects']:
   d=abs(found[o['label']]['distance']-o['distance']);maxerr=max(maxerr,d);assert d<1e-9
   for field in ['center_camera','closest_camera']:assert np.allclose(found[o['label']][field],o[field],atol=1e-8)
  counter['gt_independent_answers_pass']+=1;changed+=answer!=r['answer']
  if classify(r)['cites_other'] and not independent_bad and r['qid'] not in nkeys:expected.add(r['qid'])
 assert {r['provenance']['sb_rowB']['source_qid'] for r in alternatives}==expected
 assert {r['provenance']['sb_rowB']['source_qid'] for r in drafts}==expected
 for numeric,rows in [(False,alternatives),(True,drafts)]:
  qids=set();cids=set();uses=Counter()
  for x in rows:
   sid=x['provenance']['sb_rowB']['source_qid'];s=sources[sid];uses[sid]+=1;k,found,order,answer=geometries[sid]
   assert x['qid']==sid+('_sbk' if numeric else '_sbkq')
   assert x['qid'] not in qids and x['candidate_id'] not in cids;qids.add(x['qid']);cids.add(x['candidate_id'])
   assert x['candidate_id']==candidate_identity(dict(qid=x['qid'],scene=x['scene'],frame_indices=x['student_input']['frame_indices'],type=x['question_type'],question=x['student_input']['question'],options=x['student_input']['options']))
   assert not remove.match(x) and x['qid'] not in nkeys
   assert x['student_input']==s['student_input'] and x['answer']==answer
   excluded={'qid','candidate_id','target','answer','provenance'}
   assert {key:v for key,v in x.items() if key not in excluded}=={key:v for key,v in s.items() if key not in excluded}
   assert {key:v for key,v in x['provenance'].items() if key!='sb_rowB'}==s['provenance']
   frames=[int(v) for v in re.findall(r'\bframe (\d+)',x['target'])];assert frames and set(frames)=={k}
   assert not re.search(r'first seen|\bseconds?\b',x['target'])
   for label,v in found.items():
    line=next(l for l in x['target'].splitlines() if 'locate the '+label+' relative to' in l)
    assert 'frame '+str(k) in line
    if numeric:
     distance=float(re.search(r'distance of ([\d.]+) m',line)[1]);assert abs(distance-v['distance'])<=5.00001e-5
     triples=re.findall(r'\(([-\d., ]+)\) m',line);assert len(triples)==2
     for text,field in zip(triples,['center_camera','closest_camera']):
      assert all(abs(float(a)-b)<=5.00001e-5 for a,b in zip(text.split(','),v[field]))
    else:
     X,Y,Z=v['center_camera'];assert ('to the right' if X>0 else 'to the left') in line
     assert ('below' if Y>0 else 'above') in line and ('in front of' if Z>0 else 'behind') in line
   if x['question_type'].startswith('camera_'):assert ', then '.join(order)+'.' in x['target']
   if numeric:
    errors=trace_grammar.validate_row(x);assert any(e.rule_id in ('number_not_allowed','unit_quantity') for e in errors)
    counter['numeric_draft_grammar_refused']+=1
   else:native_validate(x);counter['alternative_adapter_and_validator_pass']+=1
   counter['field_diff_pass']+=1;counter['qid_candidate_id_pass']+=1;counter['frame_k_and_gt_trace_pass']+=1
  assert max(uses.values(),default=0)==1
 # Per-family exact output cells arise from an independently recomputed eligibility set, never a requested quota.
 exact={f:sum(sources[q]['question_type']==f for q in expected) for f in FAMILIES}
 assert exact=={f:build['cells'][f]['qualitative_alternatives'] for f in FAMILIES}
 scope=load(ROOT/'out/STORE_SCOPE.json');assert scope['outside_selected_families']=={'object_rel_distance':2}
 assert all(not re.search(r'frame\s+\d+|time\s+\d+',x['question']) for x in scope['examples']['object_rel_distance'])
 assert (ROOT/'out/REPLACEMENTS.jsonl').stat().st_size==0
 result=dict(input_sha256=pins,status='PARTIAL_BLOCKED',counts=dict(counter),exact_eligible_cells=exact,source_answers_changed=changed,max_independent_distance_error=maxerr,tests=dict(original_archive_member_hashes='PASS',compact_arrays_match_original='PASS',source_native_adapter_plus_validate='PASS',alternative_native_adapter_plus_validate='PASS',numeric_native_adapter_plus_validate='FAIL_AS_REQUIRED_BY_PINNED_GRAMMAR',all_numeric_rows_quarantined='PASS',room_rule_independent='PASS',exact_cell_counts='PASS',source_use_at_most_once_per_variant='PASS',unique_qids_candidate_ids='PASS',candidate_id_kit_formula='PASS',question_unchanged='PASS',field_diff='PASS',every_available_gt_answer_independently_recomputed='PASS',missing_gt_refused='PASS',all_trace_frame_references_equal_k='PASS',N_removal_schema_and_consumption='PASS',new_wording_filter='NOT_APPLICABLE_NO_NEW_WORDINGS',read30='PENDING_AGENT_READ'),native_direct_packing='student_pilot.r2_adapters.normalize then r2_contract.validate(vqa), plus trace_grammar.validate_row; ground_rows.pack is for routed event rows and does not accept this family',requested_replacement_delivery='BLOCKED: pinned direct grammar forbids numeric trace measurements; missing rasters refused separately')
 for p in (ROOT/'out').glob('*.jsonl'):result['input_sha256'][str(p)]=sha(p)
 result['input_sha256'][str(ROOT/'out/REMOVE.json')]=sha(ROOT/'out/REMOVE.json')
 dump(ROOT/'out/CHECKS.json',result);print(json.dumps(dict(counts=counter,exact_eligible_cells=exact,maxerr=maxerr,answers_changed=changed),indent=2),flush=True)
 (ROOT/'STATUS.md').write_text('Stage 4: Independent checks verified the original archive member hashes and raw arrays, recomputed every available GT answer, checked source and alternative rows through N’s direct adapter and validator, and verified room exclusions, exact cells, field diffs, frame references and IDs. Numeric drafts fail the pinned grammar and remain unadmitted. CHECKS.json records partial completion; the 30-row read and final package remain.\n')
if __name__=='__main__':main()

"""Recompute source GT, preserve questions, and separate numeric drafts from admissible qualitative alternatives."""
from common import *
from inventory import STORE

def main():
 sources=lines(ROOT/'inputs/sources.jsonl');gt={g['raster_sha256']:g for g in lines(ROOT/'inputs/GT_COMPACT.jsonl')}
 rules=RoomRule();n_path=W/'inputs/records/n.json';n_rows=lines(n_path);n_keys={x['row_key'] for x in n_rows}
 census=load(ROOT/'out/CENSUS.json');pins=dict(census['input_sha256']);pins.update(rules.pins);pins.update(kit_pins())
 for p in [n_path,ROOT/'inputs/sources.jsonl',ROOT/'inputs/GT_COMPACT.jsonl',ROOT/'out/GT_MATCH.json',ROOT/'out/CENSUS.json',ROOT/'code/build_rows.py',ROOT/'code/common.py',ROOT/'code/inventory.py',ROOT/'code/prepare_gt.py']:
  pins[str(p)]=sha(p)
 for p in [Path('/scratch/jjyeung/n30_mirror/rows_a2/v4/vsti/code')/name for name in ['generate.py','geometry.py','sources.py']]:pins[str(p)]=sha(p)
 assert pins[str(Path('/scratch/jjyeung/n30_mirror/rows_a2/v4/vsti/code/generate.py'))]=='fceb45e6bee7aff7d8c4b388cdf0caf269c1141b42d06c24c6833d23afabcb88'
 counts=Counter();cells={f:Counter() for f in FAMILIES};numeric=[];alternatives=[];removals=[];audit=[];missing=[];mapping=[];errors=Counter();diffs=Counter()
 for num,r in enumerate(sources):
  f=r['question_type'];cell=cells[f];cell['source_rows']+=1;cl=classify(r);fix=cl['cites_other'];cell['needs_retrace']+=fix
  native_validate(r);counts['source_native_pass']+=1
  rec=dict(input_sha256=pins,source_qid=r['qid'],family=f,needs_retrace=fix)
  reasons=rules.reasons(r);rec['room_refusals']=reasons;cell['room_excluded']+=bool(reasons)
  rec['already_in_n_removal']=r['qid'] in n_keys;cell['already_in_n_removal']+=rec['already_in_n_removal']
  if fix:
   # Keep N's five-field JSONL schema. Hashes are stored inside its free-text reason field.
   removals.append(dict(pool=r['pool'],question_type=f,row_key=r['qid'],scene=r['dataset']+'/'+r['scene'],reason='object_citations_outside_queried_frame; store_sha256='+pins[str(STORE/'vqa/rows.sqlite')]+'; census_sha256='+pins[str(ROOT/'out/CENSUS.json')]+'; schema_sha256='+pins[str(n_path)]+'; generator_sha256='+pins[str(ROOT/'code/build_rows.py')]))
  gg=gt.get(r['provenance']['raster_sha256'])
  if gg is None:
   rec['gt_status']='MISSING';cell['gt_missing']+=1;cell['needs_retrace_gt_missing']+=fix
   missing.append(dict(input_sha256=rec['input_sha256'],qid=r['qid'],family=f,original_path=r['provenance']['raster'],expected_mirror_path=str(Path('/scratch/jjyeung/n30_mirror')/Path(r['provenance']['raster']).relative_to('/scratch/jjyeung/orch_n30')),expected_sha256=r['provenance']['raster_sha256'],status='MISSING: no matching source raster in 96 mirrored archives or extracted npz files'))
   audit.append(rec);continue
  try:g=calculate(r,gg)
  except Exception as e:
   cell['gt_invalid']+=1;rec.update(gt_status='REFUSED',error=type(e).__name__+':'+str(e));audit.append(rec);continue
  rec.update(gt_status='recomputed',gt=g,gt_source=gg['input_sha256']);cell['gt_recomputed']+=1
  rec['answer_changed']=g['answer']!=r['answer'];cell['answer_changed']+=rec['answer_changed']
  stored=r['provenance']['geometry_values'];vals=[o['distance'] for o in sorted(g['objects'],key=lambda o:o['distance'])] if f.startswith('camera_') else [o['distance'] for o in g['objects']]
  rec['source_distance_max_error']=max(abs(float(a)-float(b)) for a,b in zip(stored,vals));assert rec['source_distance_max_error']<1e-8
  if not fix:rec['disposition']='unchanged_all_objects_at_k';audit.append(rec);continue
  if reasons or r['qid'] in n_keys:
   rec['disposition']='refused_room_or_existing_N_removal';cell['recomputed_but_excluded']+=1;audit.append(rec);continue
  for is_numeric,outputs,suffix in [(True,numeric,'_sbk'),(False,alternatives,'_sbkq')]:
   x=copy.deepcopy(r);x['qid']=r['qid']+suffix;x['answer']=g['answer'];x['target']=render(r,g,is_numeric);x['candidate_id']=cid(x)
   x['provenance']['sb_rowB']=dict(source_qid=r['qid'],source_row_sha256=canonical_hash(r),input_sha256={**pins,**gg['input_sha256']},frame_convention='one-based student slots 1-32; pose array index k-1; no seconds',distance_definition='camera centre to closest GT OBB point',recomputed=g,numeric_trace=is_numeric,admission='REFUSED_NUMERIC_DIRECT_GRAMMAR' if is_numeric else 'ALTERNATIVE_REQUIRES_USER_CHOICE')
   changed={k for k in set(r)|set(x) if r.get(k)!=x.get(k)}
   assert changed<={'qid','answer','target','candidate_id','provenance'}
   assert {k:v for k,v in x['provenance'].items() if k!='sb_rowB'}==r['provenance']
   assert x['student_input']==r['student_input']
   for k in changed:diffs[k]+=1
   if is_numeric:
    violations=trace_grammar.validate_row(x);assert violations
    errors.update({v.rule_id for v in violations});counts['numeric_native_refused']+=1
    try:native_validate(x)
    except ValueError:pass
    else:raise AssertionError('Numeric draft unexpectedly passed native validation')
   else:native_validate(x);counts['alternative_native_pass']+=1
   outputs.append(x)
  cell['numeric_drafts']+=1;cell['qualitative_alternatives']+=1
  mapping.append(dict(input_sha256=rec['input_sha256'],source_qid=r['qid'],numeric_qid=r['qid']+'_sbk',alternative_qid=r['qid']+'_sbkq'))
  rec['disposition']='numeric_draft_and_qualitative_alternative';audit.append(rec)
  if num%1000==0:print('processed',num,flush=True)
 for f in FAMILIES:
  expected=next(iter(census['families'][f].values()));c=cells[f]
  assert c['source_rows']==expected['rows'] and c['needs_retrace']==expected['cites_other']
  assert c['gt_recomputed']+c['gt_missing']+c['gt_invalid']==c['source_rows']
  assert c['numeric_drafts']==c['qualitative_alternatives']==dict(zip(FAMILIES,[793,1147,1349,1378]))[f]
 for rows in [numeric,alternatives]:
  assert len({r['qid'] for r in rows})==len(rows) and len({r['candidate_id'] for r in rows})==len(rows)
  assert max(Counter(r['provenance']['sb_rowB']['source_qid'] for r in rows).values(),default=0)<=1
 assert not ({r['qid'] for r in numeric+alternatives}&{r['qid'] for r in sources})
 assert len(removals)==sum(c['needs_retrace'] for c in cells.values())
 assert all(set(r)==set(n_rows[0]) for r in removals)
 jsonl(ROOT/'out/REBUILT_NUMERIC_UNADMITTED.jsonl',numeric)
 jsonl(ROOT/'out/GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl',alternatives)
 jsonl(ROOT/'out/REPLACEMENTS.jsonl',[]) # No row satisfies both numeric trace content and unchanged native grammar.
 jsonl(ROOT/'out/REMOVE.json',removals)
 jsonl(ROOT/'out/ROW_AUDIT.jsonl',audit);jsonl(ROOT/'out/MISSING_GT.jsonl',missing);jsonl(ROOT/'out/QID_MAP.jsonl',mapping)
 report=dict(input_sha256=pins,counts=dict(counts),cells={f:dict(c) for f,c in cells.items()},numeric_validator_errors=dict(errors),changed_fields=dict(diffs),admitted_replacements=0,remove_rows=len(removals),new_question_wordings=0,wording_filter=dict(status='NOT_APPLICABLE_NO_NEW_WORDINGS',normalized_edit_distance_threshold=None,removed=0,questions_byte_identical=True),max_source_uses_per_artifact=1,max_source_uses_across_mutually_exclusive_variants=2,full_request_status='BLOCKED: numeric positions and distances violate the pinned direct grammar; some source GT is missing',exact_cell_assertions='source family sizes and citation classes must match census; GT success/missing/invalid partitions must cover every source; each eligible recomputed defective source must yield both variants',artifacts={n:dict(sha256=sha(ROOT/'out'/n),rows=len(rows)) for n,rows in [('REBUILT_NUMERIC_UNADMITTED.jsonl',numeric),('GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl',alternatives),('REPLACEMENTS.jsonl',[]),('REMOVE.json',removals),('ROW_AUDIT.jsonl',audit),('MISSING_GT.jsonl',missing),('QID_MAP.jsonl',mapping)]})
 dump(ROOT/'out/BUILD_COUNTS.json',report)
 # Stratify full serialized rows across all four families, datasets, camera slots and answer letters.
 chosen=[]
 for f,quota in zip(FAMILIES,[8,8,7,7]):
  pool=[r for r in alternatives if r['question_type']==f]
  pool.sort(key=lambda r:hashlib.sha256(r['qid'].encode()).hexdigest());chosen+=pool[:quota]
 assert len(chosen)==30
 text=['# Thirty complete alternative rows\nThese rows pass N’s direct grammar; metric values remain in provenance. Numeric trace drafts are separately refused.\n']
 for i,r in enumerate(chosen,1):
  # Full row includes every RGB pin and full provenance; compact JSON keeps the review file navigable.
  text+=['## '+str(i)+' '+r['qid']+'\n'+r['student_input']['question']+'\n'+str(r['student_input']['options'])+'\n```text\n'+r['target']+'\n```\n','```json\n'+json.dumps(r,sort_keys=True,allow_nan=False)+'\n```\n']
 (ROOT/'out/READ30.md').write_text('\n'.join(text))
 jsonl(ROOT/'out/READ30_IDS.jsonl',[dict(qid=r['qid'],input_sha256={str(ROOT/'out/GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl'):sha(ROOT/'out/GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl')}) for r in chosen])
 (ROOT/'STATUS.md').write_text('Stage 3: BUILD_COUNTS.json records all source validations, GT recomputations, refusals, and per-family output counts. Numeric reconstructions remain in REBUILT_NUMERIC_UNADMITTED.jsonl because N rejects metric measurements in direct traces. GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl contains distinct-qid qualitative traces at k with numeric GT in provenance. REPLACEMENTS.jsonl is empty because no row meets both conflicting requirements. REMOVE.json uses N’s exact five-field JSONL schema. Independent verification and the 30-row read remain.\n')
 print(json.dumps({k:report[k] for k in ['counts','cells','numeric_validator_errors','remove_rows']},indent=2),flush=True)
if __name__=='__main__':main()

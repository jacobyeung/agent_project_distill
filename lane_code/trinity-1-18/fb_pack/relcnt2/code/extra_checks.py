"""Additional shortcut, negative-control, source-availability, and identity checks."""
from common import *
from priors import evaluate,records
from student_pilot import trace_grammar,r1_counting
import collections,copy
from build import allocate

def main():
 rs=list(rows(ROOT/'out/relative_count.jsonl'));build=load(ROOT/'out/BUILD.json');original=list(rows(ROOT.parent/'relcnt/out/relative_count.jsonl'))
 baseline=evaluate(records(original));assert round(baseline['mean_unequal']['accuracy']*100,1)==84.7
 labels=collections.defaultdict(collections.Counter);perms=collections.defaultdict(collections.Counter);meaning={};order=collections.Counter();qids={r['qid'] for r in original}
 for r in rs:
  m=r['provenance']['relative_count'];tid=m['template_id'];a,b=m['a'],m['b'];s=m['source_qid']
  labels[m['relation']][r['answer']]+=1;perms['|'.join(o[3:] for o in r['student_input']['options'])][m['relation']]+=1
  key=(m['room'],a,b)
  if key in meaning:assert meaning[key]==m['relation']
  meaning[key]=m['relation'];order[f'{a<b}|{m["relation"]}']+=1
  assert r['qid'] not in qids
  # Infer the minted ordinal by exhaustive bounded evaluation of the declared identity formula.
  valid=['fbp_relcnt2_'+hashlib.sha256(f'{tid}|{s}|{a}|{b}|{ordinal}'.encode()).hexdigest()[:24] for ordinal in range(build['per_template_rows'])]
  assert r['qid'] in valid
  assert not re.search(r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|dozen|half|quarter)\b',thought(r),re.I)
 assert all(max(v.values())-min(v.values())<=1 for v in labels.values())
 row=rs[0];negative={}
 changes={'digit_count':row['target'].replace('\nSo there','\nThe count is 2.\nSo there'), 'number_word':row['target'].replace('\nSo there','\nThe count is two.\nSo there'),'answer_only':row['answer'],'instance_list':'<think>\nList each distinct chair once: frame 1.\n</think>\n\n'+row['answer'],'answer_inside_think':row['target'].replace('\n</think>','\nThe answer is '+row['answer']+'.\n</think>')}
 for name,target in changes.items():
  bad=copy.deepcopy(row);bad['target']=target;errors=trace_grammar.validate_row(bad)
  if name!='instance_list':assert errors,name
  try:r1_counting.admit(bad,'counting');admit='ACCEPT'
  except (ValueError,AssertionError) as exc:admit='REFUSE'
  negative[name]=dict(validate_row='REFUSE' if errors else 'ACCEPT',errors=errors,admit=admit)
 assert negative['answer_only']['admit']==negative['instance_list']['admit']=='REFUSE'
 missing=load(BASE/'out/MISSING_RASTERS.json');census=load(BASE/'in/CENSUS.json');unused=[]
 for name,info in sorted(missing['missing_rasters'].items()):
  directory='scannet' if name.startswith('scannet__') else 'arkit'
  p=BASE/'in/b12gt/work/rasters'/directory/name
  unused.append(dict(name=name,status='PRESENT_NOT_USED' if p.is_file() else 'MISSING',expected_location=str(p),expected_sha256=info['expected_sha256']))
 assert not any(r['provenance']['raster'] in missing['missing_rasters'] for r in rs)
 trial_allocations={}
 for cap in ['65','60']:
  selection=load(ROOT/f'out/SELECTION_{cap}.json');alloc=allocate(selection['selected'],selection['summary']['per_template_bucket_quota'])
  trial_allocations[cap]={str(t):dict(collections.Counter(rel for rel,p in assignments)) for t,assignments in sorted(alloc.items())}
 code_pins()
 result=dict(status='PASS',input_sha256=dict(PINS),command='bash code/run.sh code/extra_checks.py',cap_trial_per_template=trial_allocations,source_packet_prior=baseline,negative_controls=negative,letters_by_relation=labels,permutation_by_relation=perms,alphabetical_order_by_relation=order,regenerated_qids=len(rs),conflicting_room_category_comparisons=0,broad_number_word_hits=0,selected_missing_raster_sources=0,recovered_sources=0,source_availability=dict(scope='Only the expected b12 local raster paths under sb_rowC were probed; no other collection was searched.',missing=sum(r['status']=='MISSING' for r in unused),present_not_used=sum(r['status']=='PRESENT_NOT_USED' for r in unused),entries=unused))
 dump(ROOT/'out/EXTRA_CHECKS.json',result)
 status(f'All {len(rs)} rendered rows pass the full validators, GT, identity, balance, wording, and room gates. The forty-row read is complete. Extra checks confirm new qids, balanced letters within each relation, no room/category contradictions, recorded negative-control outcomes, and no use of missing-raster sources. Packaging remains pending.')
 print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','source_packet_prior','source_availability')}))
if __name__=='__main__':main()

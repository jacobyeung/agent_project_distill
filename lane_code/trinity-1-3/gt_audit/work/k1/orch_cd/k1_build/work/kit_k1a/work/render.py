"""Render authenticated native calls; GT enters only the row classifier."""
import argparse,copy,json,math,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
sys.path.insert(0,str(gate.ROOT/'o3_cache/work/kit'))
import bindings as B,pipeline as P
def render(row,result,capture,*,expected_calls_sha256,backend_hashes,fixture=False):
 if B.digest(result['calls'])!=expected_calls_sha256:raise ValueError('Runtime call bytes differ; possible GT response injection')
 if not fixture and (result.get('synthetic') or not gate.eligible(*capture['canonical'].split('/'))):raise ValueError('Synthetic or excluded production row')
 if len(capture['anchor_slots'])!=32:raise ValueError('Require pinned RGB32')
 shas=[capture['dense_frames'][s]['sha256'] for s in capture['anchor_slots']]
 if any(not re.fullmatch('[0-9a-f]{64}',h) for h in shas) or not backend_hashes:raise ValueError('Missing provenance')
 result=copy.deepcopy(result);result['decision']=P.classify(row,result,result['mask_match'])
 if result['decision']['label']=='fallback':
  fallback=row.get('fallback',{})
  if not fallback.get('visual_evidence_verified'):
   return dict(qid=row['id'],canonical=capture['canonical'],frame_sha256=shas,backend_hashes=backend_hashes,
     calls_sha256=expected_calls_sha256,fixture_only=fixture,training_admitted=False,label='excluded',type=row['type'],reason='Runtime failure has no reviewed visual fallback trace')
  text=fallback.get('trace','')+' '+str(fallback.get('answer',''))
  if re.search(r'\b(cannot|unable|refus\w*|unknown|not seen|not enough|insufficient)\b',text,re.I):raise ValueError('Fallback ends in refusal')
  if not math.isfinite(float(fallback['answer'])):raise ValueError('Invalid fallback answer')
 e=P.train_events(row,result)
 common=dict(qid=row['id'],canonical=capture['canonical'],frame_sha256=shas,backend_hashes=backend_hashes,
   calls_sha256=expected_calls_sha256,fixture_only=fixture,training_admitted=False,
   label='excluded' if e is None else result['decision']['label'],type=row['type'])
 if e is None:return dict(common,reason=result['decision']['reason'])
 # The native ground event renderer supplies exact character spans. The trainer masks these spans.
 from student_pilot.ground_rows import render_ground
 target,spans,_=render_ground(e['events'],e['answer'])
 if re.search(r'\d+\.\d{3,}|\d+\.\d+\s*(?:deg|degrees)\b',''.join(target[s['start']:s['end']] for s in spans)):raise ValueError('Response precision differs')
 for call,event in zip(result['calls'],[x for x in e['events'] if x['kind']=='ground_response'],strict=True):
  if event['text']!='<tool_response>\n'+call['response']+'\n</tool_response>':raise ValueError('Runtime response changed')
 routing=dict(form='spec-v3.14-ground-v1',trace_revision='3.14',question_type=row['type'],category='route',events=e['events'],answer=e['answer'],tool_output_spans=spans)
 frames=[{k:capture['dense_frames'][s][k] for k in ('path','sha256')} for s in capture['anchor_slots']]
 return dict(common,question_type=row['type'],question=row['question'],answer=e['answer'],target=target,routing=routing,
   events=e['events'],tool_output_spans=spans,response_loss_weight=0.,
   loss_mask_contract='carrier_c1_routing tool_output_spans; all response delimiters included',
   student_input=dict(question=row['question'],options=[],frames=frames,frame_indices=capture['anchor_indices']),
   provenance=dict(canonical=capture['canonical'],runtime_calls_sha256=expected_calls_sha256,backend_hashes=backend_hashes))
def from_capture(c,cache,*,fit_receipt=None,fixture=False):
 cache=Path(cache);receipt=B.load(cache/'COMPLETE.json')
 if receipt['capture_sha256']!=B.digest(c):raise ValueError('Capture/cache binding differs')
 for p in receipt['files'].values():B.checked(p)
 if not fixture:
  if fit_receipt is None:raise ValueError('Eligible refit receipt required')
  fit=B.load(fit_receipt)
  if fit.get('fixture_only') is not False:raise ValueError('Fixture refit is not a production model')
  if receipt.get('eligible_refit_sha256')!=B.sha(fit_receipt):raise ValueError('Cache was not rendered with this eligible refit')
 hashes=dict(receipt['sources']);hashes['cache_receipt']=B.sha(cache/'COMPLETE.json')
 sources={r['id']:r for r in c['rows']};results=B.load(B.checked(receipt['files']['responses.json']))
 return [render(sources[r['id']],r,c,expected_calls_sha256=B.digest(r['calls']),backend_hashes=hashes,fixture=fixture) for r in results]
def write_rows(rows,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);counts={}
 for typ in sorted({r['type'] for r in rows}):
  for label in ('trust','fallback','excluded'):
   selected=[r for r in rows if r['type']==typ and r['label']==label]
   (out/(typ+'.'+label+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in selected));counts[typ+'|'+label]=len(selected)
 (out/'COUNTS.json').write_text(json.dumps(counts,indent=2)+'\n')
 return counts
def main():
 p=argparse.ArgumentParser();p.add_argument('--capture',required=True);p.add_argument('--cache',required=True);p.add_argument('--fit-receipt',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 write_rows(from_capture(B.load(a.capture),a.cache,fit_receipt=a.fit_receipt),a.out)
if __name__=='__main__':main()

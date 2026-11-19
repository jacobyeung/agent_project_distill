"""Independently audit every training row against the raw recovered source and N code."""
import copy,gzip,json,hashlib,re
from collections import Counter
from camera_contract import *

def main():
 frozen();pin(__file__);pin(ROOT/'camera_contract.py')
 report=load(OUT/'TRAINING_CHECKS.json');INPUTS.update(report['input_sha256'])
 for p in ['CAMERA_ROWS.jsonl','CAMERA_SOURCES.jsonl.gz','CAMERA_LINEAGE.jsonl','SOURCE_ADMISSION.jsonl']:pin(OUT/p)
 wordings=load(OUT/'WORDINGS.json');a=Admission()
 admitted={r['i']:r for r in map(json.loads,(OUT/'SOURCE_ADMISSION.jsonl').read_text().splitlines())}
 sources={}
 for line in gzip.open(OUT/'CAMERA_SOURCES.jsonl.gz','rt'):
  e=json.loads(line);s=json.loads(e['row']);assert s['qid'] not in sources
  assert hashlib.sha256(e['row'].encode()).hexdigest()==admitted[e['i']]['row_sha256']
  assert hashlib.sha256(e['target'].encode()).hexdigest()==admitted[e['i']]['target_sha256']
  assert admitted[e['i']]['keep'];sources[s['qid']]=(e,s)
 lineage={r['qid']:r for r in map(json.loads,(OUT/'CAMERA_LINEAGE.jsonl').read_text().splitlines())}
 counts=Counter();uses=Counter();qids=set();cids=set();diffs=Counter()
 from generator.derivgen_v7.derivgen.camera_rows import _Geometry
 from build_camera import normalized
 for line in (OUT/'CAMERA_ROWS.jsonl').open():
  x=json.loads(line);m=re.fullmatch(r'(.+)-sbca-t(\d\d)',x['qid']);assert m
  e,s=sources[m[1]];k=int(m[2]);typ=x['routing']['question_type'];uses[m[1]]+=1;counts[f'{typ}|t{k:02d}']+=1
  assert x['qid'] not in qids;qids.add(x['qid'])
  assert x['candidate_id'] not in cids;cids.add(x['candidate_id'])
  sx=copy.deepcopy(x)
  for d in [sx,sx['routing']]:d['qid']=s['qid'];d.pop('candidate_id')
  sx['student_input']['question']=s['student_input']['question'];assert sx==s
  assert set(x)-set(s)=={'candidate_id'}
  assert set(x['routing'])-set(s['routing'])=={'candidate_id'}
  assert {key for key in s if s[key]!=x[key]}=={'qid','routing','student_input'}
  assert {key for key in s['routing'] if s['routing'][key]!=x['routing'][key]}=={'qid'}
  assert {key for key in s['student_input'] if s['student_input'][key]!=x['student_input'][key]}=={'question'}
  si=x['student_input'];raw=x['routing'];i,j,n=frames(x)
  assert si['question']==wordings['training'][typ][k].format(i=i,j=j,n=n,unit='meters',options='; '.join(si['options']))
  # Independent expansion of the kit identity formula (no generator identity helper).
  payload=[x['qid'],x['scene'],si['frame_indices'],typ,si['question'],si['options'],[],raw['trace_revision'],'phrases-v3']
  cid='ground-'+hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()
  assert x['candidate_id']==raw['candidate_id']==cid
  assert not a.reasons(x)[0] and not a.reasons(s)[0]
  native_validate(s);native_validate(x);truth=geometry(x);assert geometry(s)==truth
  # Cross-check the independent SciPy recomputation against N's own pose implementation.
  native=_Geometry(raw).pair(i,j)
  for key in ['distance','turn','dx','dy','dz']:assert native[key]==truth[key]
  assert lineage[x['qid']]['recomputed']==truth
  norm=normalized(enc(x))
  for templates in wordings['heldout'].values():
   for template in templates:
    assert normalized(template.format(i=i,j=j,n=n,unit='meters',options='; '.join(si['options']))) not in norm
 assert len(qids)==len(cids)==6000 and len(counts)==120 and set(counts.values())=={50}
 assert len(uses)==6000 and max(uses.values())==1
 assert counts==Counter({k:v['actual'] for k,v in report['cells'].items()})
 bind_code();frozen()
 save(OUT/'INDEPENDENT_TRAINING_CHECK.json',dict(status='PASS',command='/scratch/jjyeung/envs/p1cpu/bin/python -B verify_camera_training.py',rows=6000,sources=6000,cells=120,rows_per_cell=50,max_source_use=1,field_diff_failures=0,candidate_formula_failures=0,native_pack_and_validate=12000,independent_geometry=12000,native_geometry_crosscheck=6000,room_exclusion_failures=0,heldout_wording_hits=0,heldout_files_byte_identical=True))
 print('PASS: 6000 rows, 6000 sources, 120 cells, all field, geometry, identity, room and wording checks')
if __name__=='__main__':main()

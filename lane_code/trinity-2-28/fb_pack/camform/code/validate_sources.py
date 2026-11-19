"""Authenticate the extract; compare real counterparts and execute native row checks."""
from pathlib import Path
import os,sys,json,gzip,hashlib,copy,re,ast
from collections import Counter
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1];TREE=ROOT/'work/new';RO=ROOT.parent/'ro/orch_n30';CAM=RO/'fb_pack/cam/out'
sys.path.insert(0,str(TREE));sys.dont_write_bytecode=True
import torch
torch.set_num_threads(16)
inputs={};seen=set()
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0])).absolute()
  if p.is_relative_to(TREE) and p.is_file():seen.add(p)
sys.addaudithook(audit)
def pin(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 inputs[str(p)]=h.hexdigest();return h.hexdigest()
def load(p):pin(p);return json.loads(p.read_text())
from student_pilot.r1_camera_trace_form import rewrite_row,rewrite_text,ROT_OLD,ROT_NEW
from student_pilot.carrier_c1_routing import check_row,c1_row
from student_pilot.r2_adapters import normalize
from student_pilot.r2_grammar import validate_program
from student_pilot.r1_training import row_check
from student_pilot.r2_contract import frame_metadata
assert pin(TREE/'student_pilot/trace_grammar.py')=='a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268'
pin(Path(__file__));pin(RO/'fb_pack/cam/work/build.py');pin(RO/'fb_pack/cam/work/common.py')
# Execute only the original literal declarations and rewrite_text function.
source_ast=ast.parse((RO/'fb_pack/cam/work/common.py').read_text())
select=[]
for node in source_ast.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('ROT_OLD','ROT_NEW','NEG') for t in node.targets):select.append(node)
 if isinstance(node,ast.FunctionDef) and node.name=='rewrite_text':select.append(node)
namespace={'re':re};exec(compile(ast.Module(body=select,type_ignores=[]),'fbp_cam_original_rules','exec'),namespace)
forms=load(CAM/'SOURCE_FORMS.json');mapping={r['source_qid']:r for r in forms['records']}
build=load(CAM/'BUILD.json');peer_path=CAM/'rows/camera_wording.jsonl';assert pin(peer_path)==build['rows']['sha256']
peers={}
with peer_path.open() as f:
 for line in f:
  r=json.loads(line);assert r['qid'] not in peers;peers[r['qid']]=r['target']
path=RO/'sb_rowA/out/CAMERA_SOURCES.jsonl.gz';assert pin(path)==forms['source']['sha256']
counts=Counter();rewrites=Counter();rules=Counter();matched=Counter();missing=[];records=[];used=set()
def answer(row):
 rt=row['routing'];typ=rt['question_type'];resp=[e['text'] for e in rt['events'] if e['kind']=='tool_response'];assert len(resp)==1
 text=resp[0]
 if typ=='camera_displacement':expected=re.search(r'distance = ([+-]?\d+\.\d+) m',text)[1]
 elif typ=='camera_rotation':expected=str(int(re.search(r'turn = ([+-]?\d+) deg',text)[1]))
 else:
  values={k:Decimal(v) for k,v in re.findall(r'(d[xyz]) = ([+-]?\d+\.\d+) m',text)}
  scores=dict(right=values['dx'],left=-values['dx'],up=values['dy'],down=-values['dy'],forward=values['dz'],backward=-values['dz'])
  opts=row['student_input']['options'];labels=[re.sub(r'^[A-Z]\.\s*','',o).strip().casefold() for o in opts]
  winner=max(range(len(labels)),key=lambda i:scores[labels[i]])
  expected=opts[winner].split('.',1)[0]
 assert str(rt['answer'])==str(rt['gt_answer'])==row['target'].rsplit('</think>',1)[1].strip()==expected,(row['qid'],expected)
 return expected
with gzip.open(path,'rt') as f:
 for line in f:
  envelope=json.loads(line);old=json.loads(envelope['row']);qid=old['qid'];lin=mapping[qid];typ=old['routing']['question_type'];counts[typ]+=1
  assert qid not in used;used.add(qid)
  assert lin['source_i']==envelope['i'] and lin['source_row_sha256']==hashlib.sha256(envelope['row'].encode()).hexdigest()
  before=copy.deepcopy(old);new,ids=rewrite_row(old);assert old==before
  oracle=copy.deepcopy(old)
  from student_pilot.carrier_c1_routing import render
  for e in oracle['routing']['events']:
   if e['kind'] in ('plan','canonical_text'):e['text'],_=namespace['rewrite_text'](e['text'])
  oracle_target,_=render(oracle['routing']['events'],oracle['routing']['answer']);assert new['target']==oracle_target
  if ids:rewrites[typ]+=1;rules.update(ids)
  else:assert new is old
  stripped=copy.deepcopy(new);stripped['target']=old['target'];stripped['routing']['tool_output_spans']=old['routing']['tool_output_spans']
  for a,b in zip(old['routing']['events'],stripped['routing']['events'],strict=True):
   if a['kind'] in ('plan','canonical_text'):b['text']=a['text']
  assert stripped==old
  for a,b in zip(old['routing']['tool_output_spans'],new['routing']['tool_output_spans'],strict=True):
   assert old['target'][a['start']:a['end']]==new['target'][b['start']:b['end']]
  expected=answer(old);assert answer(new)==expected
  raw=dict(new['routing'],schema='derivgen-row-v2',infrastructure_only=False,target=new['target'],question=new['student_input']['question'],options=new['student_input']['options'],provenance=dict(canonical=new['routing']['canonical'],alias=new['dataset']+'/'+new['scene'],source_row_sha256=new['routing']['source_row_sha256'],physical_group=new['routing']['physical_group'],frame_indices=new['student_input']['frame_indices']))
  check_row(raw)
  rgb=dict(new['student_input'],frames=[dict(p,source_index=i) for p,i in zip(new['student_input']['frames'],new['student_input']['frame_indices'],strict=True)])
  converted=c1_row(raw,rgb);assert converted['target']==new['target']
  row_check(new,'routing');frame_metadata(new['student_input']);validate_program(normalize(new))
  peer=peers.get(lin['training_qid'])
  if peer is None:missing.append(dict(source_qid=qid,expected_qid=lin['training_qid'],expected_path=str(peer_path)))
  else:assert peer==new['target'],qid;matched[typ]+=1
  records.append(dict(source_qid=qid,source_row_sha256=lin['source_row_sha256'],training_qid=lin['training_qid'],rule_ids=ids,target_sha256=hashlib.sha256(new['target'].encode()).hexdigest(),peer_status='MISSING' if peer is None else 'PASS'))
  if sum(counts.values())%1000==0:print(sum(counts.values()),dict(rewrites),flush=True)
assert len(used)==6000 and sum(matched.values())==len(peers)==5979
for p in sorted(seen):pin(p)
result=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/validate_sources.py',source_rows=sum(counts.values()),types=counts,rewritten_by_type=rewrites,rules=rules,fbp_cam_targets_equal_by_type=matched,fbp_cam_comparison='MISSING_21_COUNTERPARTS',missing_counterparts=missing,original_rule_code_equal=6000,shared_grammar_pass=6000,native_check_row_pass=6000,native_c1_row_pass=6000,native_row_check_pass=6000,native_frame_metadata_pass=6000,answers_recomputed_unchanged=6000,only_authorized_changes=6000,records=records)
(ROOT/'out/SOURCE_TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 3: All 6,000 authenticated camera sources pass the shared grammar, native camera conversion/checks, frame metadata, and printed-response answer recomputation after the overlay. Targets match all 5,979 delivered fbp_cam counterparts by its saved source-ID records; the remaining 21 counterparts are MISSING. The exact rules rewrite 2,000 rotation and 1,996 direction rows. Composition regression and complete CPU-suite comparisons remain in progress.\n')
print({k:v for k,v in result.items() if k not in ('input_sha256','records','missing_counterparts')},flush=True)

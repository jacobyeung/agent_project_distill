"""Controlled composition comparison on the authentic extract, without claiming production filtering."""
from pathlib import Path
import os,sys,hashlib,json,gzip,sqlite3,importlib.util
from unittest.mock import patch
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];TREE=ROOT/'work/new';RO=ROOT.parent/'ro/orch_n30'
sys.path.insert(0,str(TREE));sys.dont_write_bytecode=True
import torch
torch.set_num_threads(16)
from student_pilot import r1_routing as new
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
from student_pilot.r1_camera_trace_form import rewrite_row
from student_pilot.p3_provenance import file_pin
path=RO/'sb_rowA/out/CAMERA_SOURCES.jsonl.gz';root=ROOT/'work/composition';root.mkdir(exist_ok=True)
inputs={str(path):file_pin(path)['sha256'],str(Path(__file__)):file_pin(Path(__file__))['sha256']}
seen=set()
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0])).absolute()
  if p.is_relative_to(TREE) and p.is_file():seen.add(p)
sys.addaudithook(audit)
rows=[];targets=[]
with gzip.open(path,'rt') as f:
 for line in f:
  item=json.loads(line);rows.append(json.loads(item['row']));targets.append(json.loads(item['target']))
db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
for i,(row,target) in enumerate(zip(rows,targets,strict=True)):db.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps(target)))
db.commit();(root/'extract.sqlite').write_bytes(db.serialize());db.close()
# This is an explicitly labeled test fixture over the authenticated extract.
# Filters is replaced below; no scene list, train/held-out division, or admission
# evidence is synthesized. All native Rows.row checks still execute.
fixture=dict(schema=ROUTING_SCHEMA,scene_role='train',heldout_overlap=0,database=file_pin(root/'extract.sqlite'),division=None,fixture_only=True)
p=root/'fixture_base.json';p.write_text(json.dumps(dict(fixture,input_sha256=inputs)));base_pin=file_pin(p)
cfg=dict(r1_training=dict(routing_slices='deferred_first_boundary'))
spec=importlib.util.spec_from_file_location('student_pilot._camform_baseline',ROOT/'work/base/student_pilot/r1_routing.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
inputs[str(Path(spec.origin))]=file_pin(Path(spec.origin))['sha256']
def compose(module,output,config):
 with patch.object(module,'Filters') as filters:
  filters.return_value.reason.return_value=None
  return module.compose(base_pin,{},(),config,output)
output=root/'same_output_path';first=compose(baseline,output,cfg)
old_hashes={p.name:file_pin(p)['sha256'] for p in output.iterdir() if p.is_file()}
output.rename(root/'baseline_snapshot')
second=compose(new,output,cfg)
new_hashes={p.name:file_pin(p)['sha256'] for p in output.iterdir() if p.is_file()}
assert old_hashes==new_hashes,(old_hashes,new_hashes)
assert first==second and first['count']==6000 and not first['refused'],first
pin=file_pin(TREE/'configs/r1_camera_trace_form_v1.json');inputs[pin['path']]=pin['sha256']
enabled=compose(new,root/'enabled',dict(r1_training={**cfg['r1_training'],'camera_trace_form':pin}))
assert enabled['count']==6000 and not enabled['refused'],enabled
counts=Counter();untouched=Counter()
conn=sqlite3.connect('file:'+enabled['database']['path']+'?mode=ro',uri=True)
for (i,raw,target),old,prior_target in zip(conn.execute('SELECT i,row,target FROM rows ORDER BY i'),rows,targets,strict=True):
 result=json.loads(raw);expected,ids=rewrite_row(old);assert result==expected;assert json.loads(target)==prior_target
 if ids:counts[result['routing']['question_type']]+=1
 else:assert result==old;untouched[result['routing']['question_type']]+=1
conn.close()
assert dict(counts)==enabled['camera_trace_form']['rewritten_base_rows_by_type']
for p in seen:inputs[str(p)]=file_pin(p)['sha256']
result=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/compose_extract.py',fixture_scope='Authentic 6000-row extract, Filters mocked to admit all; real Rows.row validation. Not a production filter census.',absent_byte_identical=True,absent_file_sha256=old_hashes,enabled_rewrites=counts,unchanged=untouched,parallel_target_column_unchanged=6000,enabled_receipt=enabled,receipts_sha256={str(p):file_pin(p)['sha256'] for p in [root/'baseline_snapshot/receipt.json',output/'receipt.json',root/'enabled/receipt.json']})
(ROOT/'out/COMPOSITION_TESTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(dict(absent_byte_identical=True,rewrites=dict(counts),untouched=dict(untouched)),flush=True)
(ROOT/'STATUS.md').write_text('Stage 4: The extract composition test stores all 6,000 rows through the real native reader. With the field absent, the database, membership, and receipt bytes equal base+PATCH_A at the same output path. Enabled composition rewrites 2,000 rotation and 1,996 direction rows, preserves 2,004 other rows and all parallel target-column values, and records matching receipt counts. Filters were mocked to admit the extract; this is not a production census. Both full CPU suites are running.\n')

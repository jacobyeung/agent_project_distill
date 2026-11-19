"""CLI regressions; immutable prior2b fixtures retain their NONPRODUCTION labels."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

W=Path(__file__).resolve().parents[1]
FB=W.parent
OLD=FB/'prior2b'
ROOT=W/'work/checker_tests'
ROOT.mkdir(parents=True,exist_ok=True)
CHECKER=W/'out/prove_on_prepared.py'
WEIGHTS=FB/'prior2/out/TOWARD_HARD_WEIGHTS.json'
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',
         OPENBLAS_NUM_THREADS='16',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
sys.dont_write_bytecode=True
inputs={}
def pin(p):
 p=Path(p).resolve()
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 v=dict(path=str(p),sha256=h.hexdigest());inputs[str(p)]=v;return v
def load(p):pin(p);return json.loads(Path(p).read_text())
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(dict(v,inputs=list(inputs.values())),sort_keys=True,indent=2)+'\n')
 return pin(p)
pin(__file__);pin(CHECKER);pin(OLD/'scripts/test_checker.py');pin(WEIGHTS)
base=load(OLD/'work/mix_fixture/FIXTURE.json')
common=['nice','-n','10',sys.executable,str(CHECKER),'--base-tree',str(OLD/'work/sealed_base'),
        '--patched-tree',str(OLD/'work/sealed_new'),'--weights',str(WEIGHTS)]
records=[]
def run(name,extra,error):
 d=ROOT/name;d.mkdir(exist_ok=True)
 cmd=common+extra+['--output-dir',str(d/'result')]
 with (d/'stdout.log').open('w') as out:r=subprocess.run(cmd,env=ENV,stdout=out,stderr=subprocess.STDOUT)
 result=load(d/'result/RESULT.json') if (d/'result/RESULT.json').is_file() else {}
 ok=r.returncode==1 and error in result.get('error','') and result.get('production_gate')!='PASS'
 rec=dict(name=name,status='PASS' if ok else 'FAIL',expected_error=error,actual_error=result.get('error'),
          returncode=r.returncode,command=shlex.join(cmd),result=pin(d/'result/RESULT.json') if result else 'MISSING')
 records.append(rec);print(name,rec['status'],rec['actual_error'],flush=True)

for name,error in [('duplicate','DUPLICATE_SOURCE_OFFSET'),('missing','MISSING_routing_indices.json'),
                   ('hash','HASH_MISMATCH'),('incomplete','R1_COMPLETE_FILTERED_POPULATION_REQUIRED')]:
 fixture=OLD/'work/checker_negative'/name/'FIXTURE.json';pin(fixture)
 run('prior2b_'+name,['--fixture',str(fixture)],error)
run('prior2b_fixture_as_real',['--config',base['native_config']['path'],
    '--prepared-receipt',base['prepared_receipt']['path']],'FIXTURE_CANNOT_BE_USED_AS_REAL_PREPARATION')

# Execute the review's exact config and receipt, including its re-pinned scope removal.
review=FB/'priorrev/work/s6'
pin(FB/'priorrev/work/s6_unlabelled.py');pin(review/'config.json');pin(review/'receipt.json')
args=['--config',str(review/'config.json'),'--prepared-receipt',str(review/'receipt.json')]
for flag,key in [('--receipt','stream_receipts'),('--offset-table','offset_tables')]:
 for stream,p in base[key].items():args += [flag,stream+'='+p['path']]
run('review_unlabelled_fixture',args,'REAL_LAUNCH_STORE_HASHES_MISMATCH:vqa')

# A guessed vqa identity does not turn synthetic databases into production inputs.
launch=load(W/'out/N_LAUNCH_CONFIG.json')
cfg=load(review/'config.json');receipt=load(review/'receipt.json')
cfg['r1_training']['store_hashes']=copy.deepcopy(launch['r1_training']['store_hashes'])
receipt['r1_training']=copy.deepcopy(cfg['r1_training'])
d=ROOT/'spoof_vqa_identity';d.mkdir(exist_ok=True)
cfg['preparation']=put(d/'receipt.json',receipt);put(d/'config.json',cfg)
run('spoof_vqa_identity',['--config',str(d/'config.json'),'--prepared-receipt',str(d/'receipt.json')],
    'REAL_LAUNCH_PIN_MISMATCH:r1_training.store_parameter')

# Missing inputs and changed tree bytes produce named refusals before importing project code.
empty=ROOT/'empty_tree';empty.mkdir(exist_ok=True)
old_common=common
common=common.copy();common[common.index('--patched-tree')+1]=str(empty)
run('unsealed_tree',['--config',str(review/'config.json'),'--prepared-receipt',str(review/'receipt.json')],
    'REAL_PATCHED_TREE_PIN_MISMATCH')
common=old_common
run('missing_config',['--config',str(ROOT/'MISSING_config.json'),'--prepared-receipt',str(review/'receipt.json')],
    'MISSING:'+str(ROOT/'MISSING_config.json'))
put(W/'out/CLI_TESTS.json',dict(status='PASS' if all(r['status']=='PASS' for r in records) else 'FAIL',
    records=records,scope='Refusal regressions; no synthetic input can establish production PASS.',
    command=shlex.join(sys.argv)))
raise SystemExit(0 if all(r['status']=='PASS' for r in records) else 1)

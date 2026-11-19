"""Collate independently reproduced results and their input hashes."""
from pathlib import Path
import hashlib, json, sys, ast
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=Path('/scratch/jjyeung/orch_n30/sb_mask_carry')
sys.path.insert(0,str(ROOT/'kit_v2'))
import mc_common as C
import mc_track_io as IO
pins={}
def read(p):
    p=Path(p);b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
def j(p):return json.loads(read(p))
read(__file__)
static=j(HERE/'STATIC_AUDIT.json')
contracts=j(HERE/'CONTRACT_AUDIT.json')
model=j(HERE/'MODEL_AUDIT.json')
step0=j(HERE/'out/v2/dry/STEP0_PRECISION.json')
parity=j(HERE/'out/v2/dry/STUB_PARITY.json')
frames=j(HERE/'out/v2/FRAME_SETS.json')
seeds=j(HERE/'out/v2/seeds/SEEDS.json')
guard=j(HERE/'out/v2/GUARD.json')
tests=read(HERE/'logs/tests.log').decode().strip().splitlines()[-1]
preflight=read(HERE/'logs/preflight.log').decode().strip().splitlines()[-1]
for p in (ROOT/'kit_v2').glob('*'):
    if p.is_file():read(p)
for p in [HERE/'review_run.py',HERE/'review_run.sh',HERE/'reproduce.sh',HERE/'tests_run.py',ROOT/'kit_v2/tests/test_kit.py']:
    read(p)
read(ROOT/'in/v2/KIT_SPEC_mask_carry_v2.md')
read('/scratch/jjyeung/orch_n30/sb_mdrev2/REVIEW_VERDICT.md')
phrase_decision=j('/scratch/jjyeung/orch_n30/sb_mask_phrase/out/DECISION.json')
source=(ROOT/'kit_v2/mc_tracker.py').read_text()
tree=ast.parse(source)
builder_calls=[dict(line=n.lineno,keywords={k.arg:ast.unparse(k.value) for k in n.keywords}) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='build_sam3_video_model']
# A planted positive-score empty anchor demonstrates the additional membership gate.
mask=np.ones((2,2),bool);empty=np.zeros((2,2),bool)
fixture=IO.object_record(0,'synthetic',1,1,[0,1],[0,1]+[None]*30,{0:(mask,1.),1:(empty,1.)},mask)
staging_items=j(ROOT/'out/v2/STAGING.json')['items']
listed={p for i in staging_items for p in (i['path'] if isinstance(i['path'],list) else [i['path']])}
omitted=[str(ROOT/'out/v2'/n) for n in ['STAGING.json','STAGING_FRAMES.txt'] if str(ROOT/'out/v2'/n) not in listed]
result=dict(command='bash review_run.sh p1cpu final_evidence.py',commands=dict(dry_steps='bash reproduce.sh',tests='bash review_run.sh p1cpu tests_run.py',model='bash review_run.sh sam3 model_audit.py',static='bash review_run.sh p1cpu audit_static.py',contracts='bash review_run.sh p1cpu contract_audit.py',preflight='bash review_run.sh sam3 /scratch/jjyeung/orch_n30/sb_mask_carry/kit_v2/mc_preflight.py'),step0=step0['summary'],stub_parity=parity['checks'],frame_order=dict(captures=len(frames['captures']),frames=frames['unique_frames'],status=frames['status'],failures=frames['failures'],sha_mismatches=frames['sha_mismatches']),seeds=dict(check=seeds['check1'],summary=seeds['summary']),tests=tests,preflight=json.loads(preflight),model_summary={k:v for k,v in model.items() if k not in ('records','input_sha256')},model_tracks=[{k:v for k,v in r.items() if k!='anchors'} for r in model['records']],builder_calls=builder_calls,positive_empty_synthetic_fixture=fixture['anchors'][1],staging_control_files_missing_from_items=omitted,phrase_producer_bar_evidence=phrase_decision['bars'][phrase_decision['chosen_arm']],freeze=static['freeze'],archive=static['archive'],withheld=guard['lists']['withheld_80'],input_sha256=pins)
(HERE/'REVIEW_EVIDENCE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','model_summary')},indent=2))

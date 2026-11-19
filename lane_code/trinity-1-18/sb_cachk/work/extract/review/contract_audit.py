"""Synthetic, CPU-only probes of launch, resume, and phrase contracts."""
from pathlib import Path
import sys, json, os, subprocess, importlib.util, time
HERE=Path(__file__).resolve().parent
ROOT=Path('/scratch/jjyeung/orch_n30/sb_cafix')
sys.path.insert(0,str(ROOT/'kit_v2'))
import mc_common as C
import mc_track_pass as TP
import mc_phrase as PH
C.code_pins();C.pin(__file__)
raw=C.read_json(C.PHRASE_FOLDS)
parsed=PH.parse(raw)
bad=[r for r in raw['folds'] if tuple(r['phrases'])!=parsed[r['fold']][r['name']]]

# Stop before reading any real tracker input. No process is launched or killed.
class ReachedInputs(Exception):pass
events=[]
TP.event=lambda kind,**kw:events.append(dict(event=kind,**kw))
TP.read_ledger=lambda out:dict(spent_seconds=123.,runs=[],dropped=[],stopped='KILLED (synthetic review fixture)')
original_pin=C.pin
def sentinel(path):raise ReachedInputs
C.pin=sentinel
refused=TP.main(['--device','cpu','--out',str(HERE/'tmp/resume_probe')])
bypassed=False
try:TP.main(['--device','cpu','--out',str(HERE/'tmp/resume_probe'),'--resume-after-stop'])
except ReachedInputs:bypassed=True
C.pin=original_pin

# Exercise the real launcher with mocked SMI and zero wait in its documented dry-test mode.
case=HERE/'tmp/second_reading';case.mkdir(parents=True,exist_ok=True)
counter=case/'count'
smi=case/'smi.sh'
smi.write_text('#!/bin/bash\nif [ -e "'+str(counter)+'" ]; then\n echo "0, 49140, 1025"\nelse\n echo 1 > "'+str(counter)+'"\n echo "0, 49140, 0"\nfi\n')
smi.chmod(0o755)
env=dict(os.environ,MC_DRY_LAUNCH='1',MC_NVIDIA_SMI=str(smi),MC_WAIT_SECONDS='0',MC_HOST='trinity-1-18',MC_TEST_OUT=str(case/'out'),MC_SKIP_PREFLIGHT='1')
ret=subprocess.run(['bash',str(ROOT/'kit_v2/launch_gpu.sh')],env=env,capture_output=True,text=True)
ev=[json.loads(l) for l in (case/'out/EVENTS.jsonl').read_text().splitlines()]
source=(ROOT/'kit_v2/mc_track_pass.py').read_text()
seeds=C.read_json(ROOT/'out/v2/seeds/SEEDS.json')
guard=C.read_json(ROOT/'out/v2/GUARD.json')
excluded=set(guard['lists']['withheld_80']['hit_captures'])
included=[r['capture'] for r in seeds['captures'] if r['capture'] not in excluded]
result=dict(command='bash review_run.sh p1cpu contract_audit.py',synthetic_probes=True,killed=dict(default_exit=refused,override_reaches_tracker_inputs=bypassed,events=events),second_reading=dict(exit=ret.returncode,events=ev,stdout=ret.stdout),phrase=dict(rows=len(raw['folds']),mismatches=len(bad),bars_passed_field_present='bars_passed' in raw),exclude_withheld=dict(original=len(seeds['captures']),included=len(included),excluded=sorted(excluded),summary_required_captures=209,summary_required_rows=1037),input_sha256=C.all_pins())
(HERE/'CONTRACT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

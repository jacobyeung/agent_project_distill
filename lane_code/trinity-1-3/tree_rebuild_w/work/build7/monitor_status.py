import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7'
state=json.loads((B/'FINAL_PASS.json').read_text())[-1]
result=dict(step=state['step'],status=state['status'],source='work/build7/FINAL_PASS.json')
if state['step']=='package' and state['status']=='running':
 for variant in ('base','tree'):
  folder=B/'proofs'/('suite_'+variant);p=folder/'progress.json'
  if p.exists():
   active=json.loads(p.read_text());group=active.get('group')
   if group:
    result.update(variant=variant,group=group)
    p=folder/group/'progress.json'
    if p.exists():result.update(json.loads(p.read_text()))
    log=folder/group/'tests.log'
    if log.exists():
     with log.open('rb') as stream:
      stream.seek(max(0,log.stat().st_size-1024))
      lines=stream.read().decode(errors='replace').splitlines()
     if lines:result['current_log']=lines[-1]
    result['source']=str((folder/group/'progress.json').relative_to(L))
    break
print(json.dumps(result))

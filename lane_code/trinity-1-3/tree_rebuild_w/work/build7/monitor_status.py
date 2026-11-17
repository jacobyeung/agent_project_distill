import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7'
def read(path,default):
 try:return json.loads(path.read_text())
 except (OSError,json.JSONDecodeError):return default
state=read(B/'FINAL_PASS.json',[dict(step='progress_write',status='unavailable')])[-1]
result=dict(step=state['step'],status=state['status'],source='work/build7/FINAL_PASS.json')
if state['step']=='package' and state['status']=='running':
 for variant in ('base','tree'):
  folder=B/'proofs'/('suite_'+variant);p=folder/'progress.json'
  if p.exists():
   active=read(p,{});group=active.get('group')
   if group:
    result.update(variant=variant,group=group)
    p=folder/group/'progress.json'
    if p.exists():result.update(read(p,{}))
    for event in ('errors','failures'):
     live=folder/group/('live_'+event+'.json')
     value=read(live,None)
     if value is not None:result[event]=len(value)
    log=folder/group/'tests.log'
    if log.exists():
     with log.open('rb') as stream:
      stream.seek(max(0,log.stat().st_size-1024))
      lines=stream.read().decode(errors='replace').splitlines()
     if lines:result['current_log']=lines[-1]
    result['source']=str((folder/group/'progress.json').relative_to(L))
    break
elif state['step']=='targeted' and state['status']=='running':
 folder=B/'proofs/final_targeted'
 result.update(read(folder/'progress.json',{}))
 for event in ('errors','failures'):
  value=read(folder/('live_'+event+'.json'),None)
  if value is not None:result[event]=len(value)
 result['source']=str((folder/'progress.json').relative_to(L))
print(json.dumps(result))

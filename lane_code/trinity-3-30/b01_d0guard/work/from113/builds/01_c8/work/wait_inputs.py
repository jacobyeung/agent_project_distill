"""Bounded, read-only polling of governor completion markers; no transfers or retries."""
from datetime import datetime,timezone
import json,time
from pathlib import Path
B=Path(__file__).resolve().parents[1]
W=B.parents[1]/'work'
started=time.time();deadline=started+6*3600
history=[]
while True:
    now=time.time()
    present={name:(W/'streams'/(name+'.done')).is_file() for name in ('masks','geometry','np226','frames')}
    runtime=Path('/scratch/jjyeung/envs/vllm/bin/python').is_file()
    value=dict(started_utc=datetime.fromtimestamp(started,timezone.utc).isoformat(),
        checked_utc=datetime.fromtimestamp(now,timezone.utc).isoformat(),
        deadline_utc=datetime.fromtimestamp(deadline,timezone.utc).isoformat(),
        complete_markers=present,production_python_exists=runtime,
        elapsed_seconds=round(now-started,3),status='READY' if all(present.values()) else 'TIMEOUT' if now>=deadline else 'WAITING')
    history.append(value)
    (B/'out/INPUT_WAIT.json').write_text(json.dumps(value,indent=2)+'\n')
    if len(history)==1 or len(history)%10==0 or value['status']!='WAITING':
        with (B/'out/INPUT_WAIT_HISTORY.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
        print(json.dumps(value),flush=True)
    if value['status']!='WAITING':break
    time.sleep(min(60,max(0,deadline-time.time())))

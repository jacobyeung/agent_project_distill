"""Keep durable heartbeat and one-minute liveness/log-growth observations."""
import json, os, subprocess, time
from pathlib import Path
from datetime import datetime, timezone
out=Path('/data2/jjyeung/agent_project_data/student_shakedown_20260918')
coord='/home/jjyeung/agent_project/agent/coord.py'
py='/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python'
os.environ.update(AGENT_COORD_DIR='/data2/jjyeung/agent_project/.coord',AGENT_ID='student-shakedown-20260918')
previous={}; silent={}
for tick in range(1440):
    stamp=datetime.now(timezone.utc).isoformat()
    states={}
    for arm in ('answer_only','summary_plus_answer'):
        pidfile=out/arm/'train.pid'; logfile=out/arm/'train.log'
        pid=int(pidfile.read_text()) if pidfile.exists() else None
        alive=bool(pid and Path(f'/proc/{pid}').exists())
        size=logfile.stat().st_size if logfile.exists() else 0
        silent[arm]=silent.get(arm,0)+1 if size==previous.get(arm) else 0
        previous[arm]=size
        states[arm]=dict(pid=pid,alive=alive,log_bytes=size,silent_checks=silent[arm],needs_debug=alive and silent[arm]>=2)
        if tick%5==0 and alive:
            wid=f'student__shakedown_{arm}__diag73__s17__2b7032f417'
            subprocess.run([py,'-B',coord,'heartbeat',wid,'--note',json.dumps(states[arm])],check=False)
    with (out/'monitor.jsonl').open('a') as f:f.write(json.dumps(dict(timestamp=stamp,states=states))+'\n')
    if tick%5==0:
        with (out/'HEARTBEAT.log').open('a') as f:f.write(f'{stamp} | {json.dumps(states)}\n')
    if all((out/arm/'exit_code').exists() for arm in states):break
    time.sleep(60)

"""Reproduce the local shell shutdown pattern using only owned toy processes."""
import json
import os
from pathlib import Path
import subprocess
import sys

W = Path(__file__).resolve().parent
events = W / 'export_overlap.jsonl'
worker = W / 'export_overlap_worker.py'
worker.write_text('''import json,sys,time
from pathlib import Path
p=Path(sys.argv[1])
def event(kind):
    with p.open('a') as f:
        f.write(json.dumps(dict(who=sys.argv[2],kind=kind,time=time.monotonic()))+'\\n')
event('start')
time.sleep(0.6)
event('end')
''')
script = '''set -u
( "$PY" -B "$WORKER" "$EVENTS" background; : ) &
persister=$!
while [[ ! -s "$EVENTS" ]]; do sleep 0.01; done
kill "$persister"
"$PY" -B "$WORKER" "$EVENTS" final
wait "$persister" 2>/dev/null || true
'''
env = dict(os.environ, PY=sys.executable, WORKER=str(worker), EVENTS=str(events))
subprocess.run(['/bin/bash', '-c', script], env=env, check=True)
rows = [json.loads(line) for line in events.read_text().splitlines()]
times = {(row['who'], row['kind']): row['time'] for row in rows}
overlap = times['final', 'start'] < times['background', 'end']
assert overlap
print(json.dumps(dict(overlap=overlap, events=rows), indent=2))

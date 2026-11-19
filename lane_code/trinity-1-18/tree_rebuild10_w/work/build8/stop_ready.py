"""Pin the prepared external proof without rerunning its socket attempt."""
import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8';P=B/'proofs/stop_multirank'
paths=[B/'stop_multirank.py',B/'stop_monitor.py',B/'RUN_PY.sh',P/'RUN.sh',
 L/'work/tree_r1/launch_s1/b/r.sh',L/'work/tree_r1/launch_s1/b/h.py',
 L/'work/tree_r1/launch_s1/b/i.py',L/'work/tree_r1/student_pilot/carrier_c1_run.py']
for p in paths:
 if p.suffix=='.py':compile(p.read_bytes(),str(p),'exec')
(P/'RUN.sh').chmod(0o755)
value=dict(files={str(p.relative_to(L)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
 status='Prepared after the sandbox socket refusal and a separate receipt showing step one followed by a helper-path signal failure. The driver path and stale marker handling are repaired but not rerun here; full stop and reload remain unverified.',
 local_attempt='work/build8/proofs/stop_multirank/RESULT.json',next_action='lane runs RUN.sh after build 8')
(P/'DRIVER_PINS.json').write_text(json.dumps(value,indent=2)+'\n')

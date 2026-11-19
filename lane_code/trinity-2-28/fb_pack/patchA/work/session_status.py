"""Record tool-observed diagnostic session state without signalling processes."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
capture=ROOT/'work/inputs/session_observations.txt'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
observations=json.loads(capture.read_text())
sessions=[]
inputs={str(capture):sha(capture),str(Path(__file__)):sha(__file__)}
for entry in observations:
    result=entry['result']; log=ROOT/'out'/(entry['label']+'.log')
    inputs[str(log)]=sha(log)
    sessions.append(dict(session_id=entry['session_id'],label=entry['label'],
        observed_at_utc=entry['observed_at_utc'],
        status='ACTIVE' if result.get('session_id') else 'COMPLETED' if 'exit_code' in result else 'UNKNOWN',
        tool_result=result, log=str(log), used_for_final_test_comparison=False))
(ROOT/'out/SESSION_STATUS.json').write_text(json.dumps(dict(
    command='env PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B work/session_status.py',
    inputs_sha256=inputs, sessions=sessions,
    action='I did not signal or terminate these sessions; the user prohibits process termination.'),indent=2)+'\n')
print([(x['session_id'],x['status']) for x in sessions])

"""Wait for the active qualification once, then qualify the final source once."""
from pathlib import Path
import time,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build13'
while True:
    runs=json.loads((B/'FINAL_RUNS.json').read_text())
    if any(r['returncode'] for r in runs):raise SystemExit('Prior qualification failed; no automatic retry')
    if runs and runs[-1]['name']=='storage':break
    time.sleep(60)
assert 'final/packet 0' in (B/'freeze_console.log').read_text()
print('Prior qualification complete; qualifying final source',flush=True)
raise SystemExit(subprocess.run([sys.executable,'-I','-s','-B',str(B/'finalize13.py')]).returncode)

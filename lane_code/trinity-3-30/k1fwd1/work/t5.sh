K=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $K; wc -l stage_job.py phase_worker.py batch_entry.py phase_support.py job_support.py
grep -n "export\|parts\|^def \|gcloud\|destination\|artifact\|checkpoint" stage_job.py | cut -c1-220 | head -80
echo "== worker"; grep -n "export\|artifact\|checkpoint\|manifest\|^def " phase_worker.py phase_support.py | cut -c1-220 | head -80
echo "== manifest"; python3 - <<'PY'
import json
m=json.load(open('manifest_v2/a40fbc19.json'))
print(type(m), list(m.keys())[:40] if isinstance(m,dict) else len(m))
for k,v in (m.items() if isinstance(m,dict) else []):
    if not isinstance(v,(list,dict)) or len(json.dumps(v))<1500: print(k, json.dumps(v)[:1500])
    else: print(k, type(v).__name__, len(v))
PY
grep -o '.\{200\}1d6eeb28.\{200\}' manifest_v2/a40fbc19.json | head -3
grep -c 1d6eeb28 manifest_v2/a40fbc19.json; cat manifest_v2/DIFF.json

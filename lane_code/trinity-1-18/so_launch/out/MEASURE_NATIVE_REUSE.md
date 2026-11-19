# Required Orchard measurement: complete-journal reuse floor

Status: **not measured**. Run this once under the authorized Orchard CPU allocation and the existing kit namespace, after confirming that no trainer or other admission process owns this logical run. This dispatch cannot enter Orchard or read its production journal. This is a future operator procedure, not an execution request here.

Use the authenticated trainer tree, original config pin, resolved frame roots and frame-root map recorded in that node's complete `inputs/request.json`. Both phase markers and `data_receipt.json` must exist. Do not copy another node's journal, rewrite its binding, remove a marker, or change the recorded CPU count to make it pass. Existing production mode p uses 16 threads (`launch_s1/b/w.py:44–45`); that requires its own authorized Orchard CPU budget. The current dispatch allows eight threads and cannot run that request.

Inside that existing namespace, set `TRAINER` to the authenticated trainer path, `JOURNAL` to the complete logical inputs directory, and `PILOT_VENV` to the production environment. `MEASUREMENT_CPU_LIMIT` must reflect the operator's actual allocation. Obtain the required permission for production-sized full rehash I/O before running. Preserve the exact command, UTC times, stdout/stderr and exit code:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS="$MEASUREMENT_CPU_LIMIT" MKL_NUM_THREADS="$MEASUREMENT_CPU_LIMIT" \
  OPENBLAS_NUM_THREADS="$MEASUREMENT_CPU_LIMIT" TOKENIZERS_PARALLELISM=false \
  "$PILOT_VENV/bin/python" -I -s -B - <<'PY'
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, os.environ['TRAINER'])
from student_pilot import s1_admission, first_batch_progress
root = Path(os.environ['JOURNAL'])
request = json.loads((root / 'request.json').read_text())
for name in ('phase_prepare.complete.json', 'phase_frames.complete.json', 'data_receipt.json'):
    if not (root / name).is_file():
        raise RuntimeError('Complete native journal required')
if request['rehearsal'] or request['cpu_threads'] > int(os.environ['MEASUREMENT_CPU_LIMIT']):
    raise RuntimeError('Production request exceeds the authorized CPU allocation')
if request.get('frame_root_map') != os.environ.get('STUDENT_FRAME_ROOT_MAP'):
    raise RuntimeError('Use the existing node namespace and frame mapping')
original = first_batch_progress.PhaseJournal.run
reused = {}
def reuse_only(self, name, action):
    def refuse_cold(_):
        raise RuntimeError('Measurement refuses a cold phase')
    result, hit = original(self, name, refuse_cold)
    if not hit:
        raise RuntimeError('Measurement requires both phases reused')
    reused[name] = hit
    return result, hit
first_batch_progress.PhaseJournal.run = reuse_only
started = time.perf_counter()
receipt = s1_admission.admit(request['config'], root, request['frame_roots'],
    threads=request['cpu_threads'], sample_size=request['sample_size'],
    memory_gib=30, prepare_only=True)
elapsed = time.perf_counter() - started
if reused != {'prepare': True, 'frames': True} or receipt['status'] != 'PREPARED':
    raise RuntimeError('Native reuse did not complete')
print(json.dumps({'native_reuse_seconds': elapsed, 'phases_reused': reused,
                  'cpu_threads': request['cpu_threads'], 'journal': str(root)}))
PY
rc=$?
date -u
printf 'EXIT: %s\n' "$rc"
```

The hook only refuses cold actions; native `PhaseJournal.run` still verifies its binding and every output pin. Native `admit` still calls `pinned()`, `run.prepared` and `verify_frames`, and creates its usual attempt directory. No training or first-batch forward runs with `prepare_only=True`. Any refusal makes this an invalid measurement; retain it and investigate without a retry loop.

Also record the unique prepared-object bytes, frame count, host, request/marker SHA256 values and whether storage was warm. Do not evict the page cache. Report native reuse wall time separately from staging, import/preflight and network fetch. This same-node measurement is an adoption floor; it cannot prove cross-node frame portability or net savings. The so_xstore build must additionally measure verified fetch and local adoption on a second node.

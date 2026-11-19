# Exact coordinator sequence

These commands belong to the coordinator. The build agent has not executed SSH or any target-node command. All 21 archive parts are staged. The kit checks their pins itself. All eight cards are busy; staging can finish while the read waits for a free card.

In the existing **trinity-2-28** session, refuse an existing kit path before shipping. If this check fails, stop and resolve the existing delivery; do not merge deliveries or retry the transfer.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit2
if ! test ! -e "$kit_dir"; then
  echo 'REFUSED: kit path must be absent before shipping' >&2
  exit 2
fi
```

On **trinity-1-18**, submit this push through the coordinator's rate limiter, reusing its existing SSH master. Use this direction and command; do not pull from 2-28. If the transfer fails or drops, stop without a retry.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-1-18
tar -C /scratch/jjyeung/orch_n30/so_reads228/out -cf - . | timeout 600 ssh -o ConnectTimeout=20 trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/reads228/kit2 && tar -C /scratch/jjyeung/orch_n30/reads228/kit2 --skip-old-files -xf -'
date -u
```

As a **separate step on trinity-2-28**, verify the delivery manifest before executing the kit. This uses the existing target session and opens no SSH connection.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit2
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
nice -n 10 /usr/bin/python3 -I -s -B - "$kit_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'DELIVERY_MANIFEST.json').read_text())
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='DELIVERY_MANIFEST.json'}
assert actual==set(manifest['files']),sorted(actual^set(manifest['files']))
for name,spec in manifest['files'].items():
    path=root/name
    assert path.is_file() and not path.is_symlink(),name
    assert path.stat().st_size==spec['bytes'],name
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    assert digest.hexdigest()==spec['sha256'],name
print('DELIVERY_MANIFEST verified: '+str(len(manifest['files']))+' files')
PY
date -u
# One stage-only sequence: hashes, runtime extraction, input extraction, code install,
# namespace check, preparation, stage check, and the exact operator import probe.
bash "$kit_dir/coordinator228.sh" --stage-only
date -u
```

The stage-only sequence never queries a card or creates a run directory. It reads all three runtime archives before creating any runtime member, then extracts every registered group under `reads228/private_rt/`. The `x/` helpers stay there as records and have no namespace bind or execution path. Extraction logs go under `reads228/extraction_logs`; inputs and source go under `reads228/private/b01ec87a6f29b`. The package sees the pinned logical path through its namespace bind. The shared logical root is not a staging source.

Once a card is free, set `CARD` to that single index or UUID and run the following **once on trinity-2-28**. Do not issue a separate manual idle gate: this invocation owns the UUID lock, takes both readings at least 300 seconds apart, and starts the worker. A busy-card refusal after the run directory exists consumes that name; any later authorized attempt needs a fresh name.

```bash
set -euo pipefail
date -u
test "$(hostname -s)" = trinity-2-28
kit_dir=/scratch/jjyeung/orch_n30/reads228/kit2
stage=/scratch/jjyeung/orch_n30/reads228
test -n "${CARD:?Set CARD to the chosen free index or UUID}"
bash "$kit_dir/coordinator228.sh" --run-only "$CARD" "$stage/runs/a400check1"
date -u
```

`--run-only` rehashes staged data and checks operator imports before the card gate; allow minutes of local scratch IO before the first idle reading. It invokes `run228.sh` exactly once with `--items 50`, compares against `kit2/reference`, unpacks with the unchanged unpacker into `kit2/ingest/a400check1`, and writes `CORPUS_INGEST.json`. A clean 50/636 return has `EXIT.status=FAILED`; ingestion uses `SUMMARY.failure=null`, completion and the comparison result. A diagnostic comparison cannot publish READY_FOR_CORPUS. A failed run stops this sequence and is not retried.

The coordinator-authorized second `--stage-only`, from `kit2` after the reported refusal, starts with an absent `private_rt/`. It verifies the same 13 runtime part pins, completes pass 1 across r0/r1/r2, creates the private runtime in pass 2, extracts inputs into the private logical root, installs sealed code, probes the namespace, prepares once, verifies staging and probes operator imports. It never reads or removes the 443 entries left in shared `orch_cd/` by the refused delivery. The old `kit/` stays in place.

A subsequent authorized stage check on a successfully staged kit compares every existing runtime file and symlink in pass 1, preserves matching files and their metadata in pass 2, skips matching input members, verifies installed code, and reuses READY.json instead of launching preparation again. A conflict refuses before runtime writes. There is no retry loop; an interrupted extraction or failed preparation requires coordinator review before another invocation.

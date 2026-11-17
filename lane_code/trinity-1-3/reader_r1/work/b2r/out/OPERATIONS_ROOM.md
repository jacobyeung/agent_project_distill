Package `c3cc59fb4aae0` runs one development-only, 134-item room read at SFT step 544. The read uses tower, mode none, null_argmax, memo on for G3T only, no verification IDs, and no own-depth output. R0-dev must never supply fitting data.

The allocated Orchard CPU check must pass before submission. It runs the first dev-S1 and first R0-dev item after authenticated staging and export restore. Local fixtures validate the check implementation; they do not authenticate Orchard-only dev-S1 image bytes. No Orchard check or GPU run occurred in this lane.

Place the delivery from an existing opaque delivery directory. Set `D` to that directory. These are operator commands; this lane ran none of them.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/c3cc59fb4aae0
printf '%s  %s\n' 741a362d5abd06124f3cff004123396ba43e8446e51883f0af955455f4b40d97 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
```

Coordinate staging IO before this allocated CPU check. It requests eight CPUs and no GPU. The helper creates a fresh private root, authenticates archives, restores the export, then runs both items through real launch, mixed native mapping, SHA256 verification, PNG decoding, ParityGenerator, CallHook, the decode loop and official scoring. Model forward, weights, tokenizer, prompt tensors, audit enforcement and decode budget use explicit CPU stubs. Any failure exits nonzero and prevents a passing CPU receipt. The allocation matches W5: general, eight CPUs, 200G, four hours, no GPU. The four-hour limit permits staging; it is not a timing estimate.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apc3cc59fb4aae0 --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

Read and verify the pass flag and both finished records after the CPU command exits successfully. `CPU.json` embeds the records under `full_reader.records`; `FULL_READER.json` repeats that proof. These scores validate the stub path, not model quality.

```bash
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['full_reader_passed'] is True
assert c['full_reader']['passed'] is True and c['full_reader']['device']=='cpu'
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
rows=c['full_reader']['records']
assert [(r['set'],r['item']) for r in rows]==[('dev-S1','room_scene0155_00'),('R0-dev','r0_015bd4aaf6870d79bade')]
assert all(r['passed'] is True and r['record']['complete'] is True and r['record']['output']['finish']=='eos' for r in rows)
print('full_reader_passed=true')
for r in rows:print(r['set'],r['item'],r['record']['output']['finish'],r['ground_truth_score']['score'])
PYCODE
```

Submit only after this command passes. The bootstrap also refuses receipts without `full_reader_passed=true`, the full-reader pass, matching payload, plan, inputs and operator hashes, and the passing memory bound. Record the shared return pool's current usage in the operator ledger; the production write test checks capacity before staging. Check the H100 resource type and pending priority jobs, then submit one GPU for 02:30:00.

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PYCODE'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu)
PYCODE
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PYCODE'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows)
PYCODE
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 02:30:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

Fetch after publication. The original pool and GCS transport remain pinned to W5.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('c3cc59fb4aae0'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer only `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W6's `work/f/`. No transfer ran here. On Trinity, unpack and score:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b2r
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/room_pair.py \
  --return-root work/ret --out out/scores
```

The scorer reports per-item MRA, dev-S1 (36), R0-dev (98), and all (134), plus capped reads and recorded malformed-call diagnostics. It recomputes MRA against each item's ground_truth with the unchanged official scorer. It pairs by exact ID and physical-room key, rejects changed bindings and duplicates, and lists missing items without inventing scores. A partial return remains explicitly incomplete. `--allow-fixture` is reserved for the synthetic test.

The stop margin is 1,800 seconds; the return margin is 1,200 seconds within it. The read estimate is 3662.6 seconds, staging/loading is 1,920 seconds, and the minimum total is 7382.6 seconds. Two hours fails; 02:30:00 leaves 1617.4 seconds of estimated slack. Price is 2.5 H100-hours plus the CPU check; no hourly rate was supplied.

The row estimate is 2,492,400 raw bytes and 428,800 compressed bytes. Adding 10,000,000 bytes for metadata and logs gives a 10,428,800-byte planning estimate, below the 89,900,000-byte archive allowance and 100,000,000-byte shared pool cap. These are estimates, not measured production returns. Shared pool occupancy can still prevent a return.

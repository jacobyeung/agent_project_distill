Package `e09e45fda45db` runs read 1 first, followed by read 0 in a separate process. Both list only `g3t` in `perception_memo_modules`. Read 1 uses `candidates_argmax`, distance only, and `verify` on its explicit first 30 distance IDs. Read 0 uses `null_argmax` and memo `on`, with distance, displacement, rotation, movement direction, then room. `READ_PLAN.json` contains the exact IDs. Each read keeps separate settings, identity, journals, and call caps.

The full-plan proxy estimate is 5.167 hours including 30 minutes for staging/loading and a 30-minute stop margin. The 20-minute return margin lies inside that stop margin. Under a five-hour allocation, the expected cut is in room after all 750 distance/camera items and about 14 room items. SAM encodes freshly whenever a read requests it; encode time is unmeasured and no SAM savings are credited. The expected room cut has 381.279 seconds of pre-room slack; unmeasured overhead can move it earlier.

Place the delivery from an existing opaque directory and check metadata. Set `D` to that directory. These commands have not run in this lane.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/e09e45fda45db
printf '%s  %s\n' eadaba88d737c4b384e3fe6908c0420a35d78c3be6037b8302d154c7109f6fc4 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

Coordinate staging IO before the allocated empty-root CPU check. This requests eight CPUs and no GPU. The helper restores authenticated inputs, checks default and per-read settings, rehearses selector wiring, and writes `a/c/CPU.json` and `a/c/MEMORY.json`. It checks the fixed G3T memo bound against 200 GiB without loading SAM for a memory measurement. The bootstrap requires the passing receipt bound to this payload, input descriptor and operator. A real evaluation-item decode remains outside this check.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape09e45fda45db --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

After the CPU check passes, use the existing review requirements and accept the documented partial-run estimate before submitting. Record the shared return pool's usage; the production write test checks its capacity before staging. The following commands check resource types and pending priority jobs, then submit one GPU for five hours.

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
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

Fetch after the return is published. The transport may mark a clean partial return as failed because the full plan did not finish; inspect its summaries.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('e09e45fda45db'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W5's `work/f/`. No transfer ran here. Unpack and score locally:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1g
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out out/tower_results
```

Unpacking rejects a missing journal or environment for a started segment. Pairing rejects missing journals, mixed rules, mismatched module bindings and changed code hashes. Partial camera journals cannot establish the complete camera comparison. Candidate-rule comparisons remain in-sample. No cross-rule journal merge is permitted.

# Two-read operator kit

Package `c91bb8ec884e9` requests one GPU on `general`. These commands have not run. The strict zero-new-findings static gate has not passed: EAT-1 adds 17 bookkeeping flags and no A4 flags. Read `EAT1_GATE.json` before any release decision. Submit only after the orchestrator's GO, the cross-family review, and the registered production-proof ordering. Main has priority; one distillation job may run at a time.

The allocation plans 636 baseline tower reads with `null_argmax` and 150 distance tower reads with `candidates_argmax`. Both use mode `none`, SFT step 544, and `save_own_depth=false`. Distance retains six calls per read; room retains two. The wrapper runs distance under both rules first, then the three camera types in their registered order, then room. Read 0 owns the baseline settings and identity; read 1 owns the candidate-only settings and identity. Each type has a separate journal below its read directory.

The segment-local estimate is **4.95 hours of reads**, or **5.95 hours including 30 minutes for staging/loading and the 30-minute stop margin**. Full coverage does not fit the five-hour cap under this estimate. The stop and return margins overlap: admission stops 30 minutes before the deadline, draining ends 20 minutes before it, and return uses the final 20 minutes.

A hypothetical single worker with shared capture values would need 3.84 hours of reads, or 4.84 hours with the same allowances. The production runner starts a new worker for every type, so this kit keeps one process per segment. It cannot reuse read 0's distance encodings in read 1. Estimates assume no eviction and do not credit unmeasured SAM savings; they are not live GPU measurements.

Read 0 uses `perception_memo=verify`, `perception_memo_verify_reads=30`, and `perception_memo_verify_types=["object_abs_distance"]`; its later reads use effective mode `on`. Read 1 uses `perception_memo=on`. Each process may retain up to 64 GiB of array/tensor payload. The first 30 distance items span 11 captures in the registered order. Items are not reordered. The policy is identical across read 0's segments and enters each journal binding. On resume, verification follows the original item ordinal. Each read starts fresh perception after a process-wide verification mismatch. The mismatch and every verified hit are recorded under `output.perception_memo` in the ordinary item journal.

GPU price is at most `5 × the approved USD/H100-hour rate`. No dollar rate was supplied, and no network lookup was authorized. The separate CPU check adds CPU charges at the operator's rate. `TIME_PRICE.json` records measured inputs and assumptions.

## Placement and unchanged staged inputs

Transfer only `out/1.tgz` through the approved operator channel, keeping the remote archive name `1.tgz` in an opaque directory. Set `D` to that existing Orchard delivery directory. Do not transfer the descriptive workspace tree. Public paths, job names, command arguments, environment values, and log names remain opaque. Descriptive reader modules and settings remain inside the sealed package and private dispatcher, as in the reviewed package.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the opaque delivery directory}"
P=/project/community/jjyeung/c91bb8ec884e9
printf '%s  %s\n' 5aa955de84d7f2c35831c6d31b24bc4c5bc864751f2d7bea9ca983c39debfa25 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
```

The delivery contains the generated package, authenticated operator helpers `a/5.py` and `a/6.py`, `a/1.json`, and `a/export.json`. Preserve their bytes. The inputs remain byte-identical to W2 and retain a null resume. The operator wrapper seals the memo schedule. The production builder constructs `0.tgz`; the operator build seals the sequence wrapper into `BATCH.sh` and updates its package descriptor.

The inputs reference these already staged files. Do not download or duplicate them:

| Parts | Whole SHA256 |
|---|---|
| `/project/community/jjyeung/okh7/e6fc152498/e/0..3` | `3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7` |
| `/project/community/jjyeung/okh7/e6fc152498/g/0` | `6a53059fc74f76a928e83da46e3b07301ff7176f69800e4ae3842599b9b57dbf` |
| `/project/community/jjyeung/okh7/e6fc152498/a2.tar` | `1de93f61bde6cf5a0a4bf7a249b13218f8b20acf4fe626c5d8ec7570ef7915e9` |
| `/project/community/jjyeung/okh7/e6fc152498/a4.tar` | `c867d40addcf35c55db1ec511c4dc2b8a4cec80cef9003be93179ef82c30b0ea` |
| `/project/community/jjyeung/okh7/e6fc152498/a3.tar` | `05dc8f79707a51ec227f4bb875670a5d3b7cfa27271447783bf2f79b7474f5ae` |

All part hashes, byte counts, preparation pins, environment pins, policy paths, and inventory declarations remain those in W2's step-544 inputs. The export pin file is unchanged. No `fill_export` invocation is needed for this already authenticated export. Its lineage is **SFT**, not RL.

## Metadata and full CPU check

```bash
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

This writes the metadata receipt `2.json`. It checks the exact package, input declarations, and staged part sizes. It does not establish restore success.

Run the full check once, alone, in the real node environment. It performs substantial project-disk staging; the operator must coordinate this IO. It authenticates archives, restores the export, prepares the runtime, and rehearses both settings, worker arguments, the explicit memo/rule settings, and the tower selector socket with stub weights. It does not decode a real item. A killed check must not be relaunched without resolving its cause.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apc91bb8ec884e9 \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

The empty-root CPU check writes `a/c/CPU.json`. The GPU bootstrap refuses if that receipt is absent or differs in payload, plan, raw inputs, or operator hash. Do not replace this receipt with the local fixture rehearsal.

## Placement proof and GPU submission

The unchanged submit helper requests generic `gpu:1`. Proceed only if the current `general` resources are explicitly typed H100 throughout. If types are absent or mixed, stop; this kit does not prove H100 placement in that case.

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PY'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu)
PY
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PY'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows), 'Pending priority job; stop'
PY
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

The GPU job name is exactly `a15_cot_apc91bb8ec884e9`. Both invocations use `general`; the first has no GPU request and the second requests one GPU. Check status at most once per minute. No retry or automatic resubmission is authorized by this kit. The production job still enforces private storage, archive hashes, preparation, admission, GPU count/time bounds, and result return.

## Fetch and score

After the job returns, fetch the bounded archive using the unchanged helper. A clean deadline stop can have transport status `FAILED` because the complete-plan marker is absent; inspect `SUMMARY.json`, which distinguishes a partial read from a worker failure.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PY'
import sys
print('c91bb8ec884e9'+format(int(sys.argv[1]),'08x'))
PY
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Use the approved return channel to place fetched `0.tgz` and `EXIT.json` at `W3/work/f/`. The remaining commands run locally in W3, using the delivered package's unchanged scorers and statistics. They do not run on Orchard.

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1m
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/0 --tower-candidates work/ret/1 \
  --out out/tower_results
```

Read `out/tower_results/TOWER_ARM_DEVS1.md` and `curve.json`. The report pairs exact item IDs, checks room and type, refuses duplicate keys, mixed rule identities, and code hashes from another evaluator. It lists missing keys and withholds a camera take-over conclusion unless that type has all 150 paired items. The bar is a lower 95% bound above −5 percentage points for own minus tower. Bootstrap uses rooms, 10,000 draws, and seed 20261115.

If staging fails before journals exist, retain the failure receipt and logs. Do not substitute self-check data or issue a pairing conclusion. A partial report is a diagnostic artifact, not a complete read or an admission receipt.

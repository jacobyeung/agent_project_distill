# Step-544 two-read operator kit

Package `e47d0593fefec` requests one GPU on `general`. These commands have not run. Submit only after the orchestrator's GO, the cross-family review, and the registered production-proof ordering. Main has priority; one distillation job may run at a time.

The allocation plans 636 baseline tower reads with `null_argmax` and 150 distance tower reads with `candidates_argmax`. Both use mode `none`, SFT step 544, and `save_own_depth=false`. Distance retains six calls per read; room retains two. The wrapper runs distance under both rules first, then the three camera types in their registered order, then room. Read 0 owns the baseline settings and identity; read 1 owns the candidate-only settings and identity. Each type has a separate journal below its read directory.

The conservative estimate is **7.61 hours of reads**, plus at least 0.50 hours for staging, restore, and model loading. The 2.5–3-hour target is unsupported. The unchanged package cap permits **one five-hour allocation**, with no new reads in the last 30 minutes and a final ten-minute drain window before the last 20 minutes reserved for return. Both distance reads need about 3.78 hours before overhead. Full camera and room coverage is not expected in this allocation. Slow staging may also prevent complete distance coverage. A partial return remains partial; these commands never join different rules or manufacture complete coverage.

GPU price is at most `5 × the approved USD/H100-hour rate`. No dollar rate was supplied, and no network lookup was authorized. The separate CPU check adds CPU charges at the operator's rate. `TIME_PRICE.json` records measured inputs and assumptions.

## Placement and unchanged staged inputs

Transfer only `out/1.tgz` through the approved operator channel, keeping the remote archive name `1.tgz` in an opaque directory. Set `D` to that existing Orchard delivery directory. Do not transfer the descriptive workspace tree. Public paths, job names, command arguments, environment values, and log names remain opaque. Descriptive reader modules and settings remain inside the sealed package and private dispatcher, as in the reviewed package.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the opaque delivery directory}"
P=/project/community/jjyeung/e47d0593fefec
printf '%s  %s\n' 1a60c9826f8d3d49081930e12dcf5434a3a876af805c2570585c7c29d4b98c03 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
```

The delivery contains the generated package, authenticated operator helpers `a/5.py` and `a/6.py`, `a/1.json`, and `a/export.json`. Preserve their bytes. The inputs change only type selection and retain a null resume. The production builder constructs `0.tgz`; the operator build seals the sequence wrapper into `BATCH.sh` and updates its package descriptor.

The inputs reference these already staged files. Do not download or duplicate them:

| Parts | Whole SHA256 |
|---|---|
| `/project/community/jjyeung/okh7/e6fc152498/e/0..3` | `3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7` |
| `/project/community/jjyeung/okh7/e6fc152498/g/0` | `6a53059fc74f76a928e83da46e3b07301ff7176f69800e4ae3842599b9b57dbf` |
| `/project/community/jjyeung/okh7/e6fc152498/a2.tar` | `1de93f61bde6cf5a0a4bf7a249b13218f8b20acf4fe626c5d8ec7570ef7915e9` |
| `/project/community/jjyeung/okh7/e6fc152498/a4.tar` | `c867d40addcf35c55db1ec511c4dc2b8a4cec80cef9003be93179ef82c30b0ea` |
| `/project/community/jjyeung/okh7/e6fc152498/a3.tar` | `05dc8f79707a51ec227f4bb875670a5d3b7cfa27271447783bf2f79b7474f5ae` |

All part hashes, byte counts, preparation pins, environment pins, policy paths, and inventory declarations remain those in bf94's step-544 inputs. The export pin file is unchanged. No `fill_export` invocation is needed for this already authenticated export. Its lineage is **SFT**, not RL.

## Metadata and full CPU check

```bash
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

This writes the metadata receipt `2.json`. It checks the exact package, input declarations, and staged part sizes. It does not establish restore success.

Run the full check once, alone, in the real node environment. It performs substantial project-disk staging; the operator must coordinate this IO. It authenticates archives, restores the export, prepares the runtime, and rehearses both settings, worker arguments, and the tower selector socket with stub weights. It does not decode a real item. A killed check must not be relaunched without resolving its cause.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape47d0593fefecc \
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

The GPU job name is exactly `a15_cot_ape47d0593fefec`. Both invocations use `general`; the first has no GPU request and the second requests one GPU. Check status at most once per minute. No retry or automatic resubmission is authorized by this kit. The production job still enforces private storage, archive hashes, preparation, admission, GPU count/time bounds, and result return.

## Fetch and score

After the job returns, fetch the bounded archive using the unchanged helper. A clean deadline stop can have transport status `FAILED` because the complete-plan marker is absent; inspect `SUMMARY.json`, which distinguishes a partial read from a worker failure.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PY'
import sys
print('e47d0593fefec'+format(int(sys.argv[1]),'08x'))
PY
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Use the approved return channel to place fetched `0.tgz` and `EXIT.json` at `W2/work/f/`. The remaining commands run locally in W2, using the delivered package's unchanged scorers and statistics. They do not run on Orchard.

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1p
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own in/h10own/170631/items.jsonl in/h10own/170706/items.jsonl in/h10own/170694/items.jsonl \
  --tower-null work/ret/0 --tower-candidates work/ret/1 \
  --out out/tower_results
```

Read `out/tower_results/TOWER_ARM_DEVS1.md` and `curve.json`. The report pairs exact item IDs, checks room and type, refuses duplicate keys, mixed rule identities, and code hashes from another evaluator. It lists missing keys and withholds a camera take-over conclusion unless that type has all 150 paired items. The bar is a lower 95% bound above −5 percentage points for own minus tower. Bootstrap uses rooms, 10,000 draws, and seed 20261115.

If staging fails before journals exist, retain the failure receipt and logs. Do not substitute self-check data or issue a pairing conclusion. A partial report is a diagnostic artifact, not a complete read or an admission receipt.

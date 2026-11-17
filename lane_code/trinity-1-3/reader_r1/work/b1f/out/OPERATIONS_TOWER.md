Package **a9439d0fb0487** runs two isolated workers in one allocation. Read 0 keeps one generator and memo across distance, camera displacement, camera rotation, camera movement direction, and room; read 1 runs distance only. Read 0 has 636 items under `null_argmax`; read 1 has 150 under `candidates_argmax`. The settings explicitly list the first 30 scheduled distance IDs for verification in read 0. Its other IDs use memo `on`; read 1 uses `on` throughout. `READ_PLAN.json` contains the complete ID list.

The package is a review deliverable. Its local required gates pass, but its 5.167-hour estimate exceeds the five-hour cap and its real SAM memory footprint has not been measured. Production readiness remains unestablished. No job, network operation, SSH, Git command, or process kill ran in this task.

The delivery contains the payload and sealed operator helpers. Input declarations and step-544 SFT export pins remain byte-identical to W3/W2. Reuse their existing staged archives; preserve the fixed private logical namespace required by the policy receipt. Transfer only `1.tgz` into an opaque delivery directory. Public job names are `a15_cot_apa9439d0fb0487`. Descriptive modules and settings remain inside the sealed payload and private dispatcher.

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the existing opaque delivery directory}"
P=/project/community/jjyeung/a9439d0fb0487
printf '%s  %s\n' 50c7ae132db7ba3960a7c123420a7eadf6aaf9a85e416d5964bdf2e5cc1ffa79 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

Run the allocated empty-root CPU check once, after coordinating its staging IO. This command requests no GPU. It authenticates and restores the inputs, checks both read settings, rehearses selector wiring, and measures one real SAM encoding in CPU float32. It writes `a/c/CPU.json` and `a/c/MEMORY.json`; the bootstrap requires a measured, fitting memory receipt bound to this payload and operator. It does not decode a real evaluation item.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_apa9439d0fb0487 --cpus-per-task=8 --mem=200G \
  --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

The submission command below remains conditional on the memory check, existing review requirements, and acceptance of a partial result under the five-hour cap. The current estimate does not support completing all 786 reads. Record the shared return pool's usage before submitting; the production write test also checks capacity before staging. Check the current `general` resource types and pending priority jobs:

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

Fetch after the return is published. The transport can label a clean partial result as failed because it lacks full-plan completion. Its summaries distinguish that case from a worker failure.

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PYCODE'
import sys
print('a9439d0fb0487'+format(int(sys.argv[1]),'08x'))
PYCODE
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

Transfer the bounded `a/f/0.tgz` and `a/f/EXIT.json` through the authorized operator channel into W4's `work/f/`. No transfer ran here. Then unpack and score locally:

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1f
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own ../b1p/in/h10own/170631/items.jsonl ../b1p/in/h10own/170706/items.jsonl ../b1p/in/h10own/170694/items.jsonl \
  --tower-null work/ret/metadata/reads/0 \
  --tower-candidates work/ret/metadata/reads/1 \
  --out out/tower_results
```

A started segment without a journal makes unpacking fail. A journal-less read makes pairing fail. Valid partial journals remain partial; missing items cannot establish the camera comparison bar. Candidate-rule differences are in-sample.


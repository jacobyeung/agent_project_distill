Package `bf94a7976a7e9` reads operator-pinned exports. It keeps the production project-disk staging path. No GCS downloader runs inside the evaluator job. All commands below run on Orchard; none ran during this build.

The H1-1 preparation receipt and m100 export are required before submission. The supplied receipt hash is `247671798be1b91e6594d3ba2b49d8659e2435830092b63352f8645bf6402d1a`. The supplied prepared config hashes to `65519f6f6399428615da3439e203e95a49967c6a2c6a73deac724696be061de2`. Do not substitute the admission request's `9385cc71…` config or the run binding's `26a60a5c…` identity for that file hash.

Set `DELIVERY` to the Orchard copy of this workspace, containing `out/` and `in/h1_1_run_inputs/`. Place the eventual real receipt at `in/h1_1_run_inputs/inputs/prepare_b000cf6bbd2346a59dc1d213e84ad066/prepared/s1_receipt.json`. Preserve the production package and dependency archives at their existing project paths.

```bash
set -euo pipefail
: "${DELIVERY:?Set DELIVERY to the copied workspace on Orchard}"
P=/project/community/jjyeung/bf94a7976a7e9
RUN="$DELIVERY/in/h1_1_run_inputs"
PREP="$RUN/inputs/prepare_b000cf6bbd2346a59dc1d213e84ad066"
test -f "$PREP/prepared/s1_receipt.json"
mkdir -m 700 "$P"
install -m 600 "$DELIVERY/out/package/"{0.tgz,0.json,3.py,BATCH.sh,CONFIG.json,SUBMIT.cmd,PACKAGE.json,INPUTS.example.json} "$P/"
mkdir -m 700 "$P/a" "$P/a/e"
install -m 600 "$DELIVERY/out/fill_export.py" "$P/a/4.py"
install -m 600 "$DELIVERY/out/node_check.py" "$P/a/5.py"
install -m 600 "$DELIVERY/out/submerge.py" "$P/a/6.py"
```

Pull the four ordered parts sequentially onto the project disk. This uses the same staging route as the supplied `b.sh`. A failed transfer stops the command; do not relaunch a killed transfer without resolving the cause.

```bash
export CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
OBJECT=q8/8865619b/17c4ffa4_m100.tar
DONE=/project/community/jjyeung/okh7/x_3fdda0fb/o/gcs_17c4ffa4_m100.done
test -f "$DONE"
for i in 0 1 2 3; do
  test ! -e "$P/a/e/$i"
  gsutil -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$P/a/e/$i"
done
```

Fill the pins on the login node with standard-library Python. The helper streams the four parts without creating a joined copy. It refuses a wrong `.done` object, total byte count, or SHA256, inconsistent artifact/member hashes, weight hashes, or incompatible preparation metadata. It writes a small metadata archive at `a/e/4` and replaces only export-related entries in the supplied H1-0 inputs; all other dependency pins and logical paths remain intact. It selects the complete camera prefix and clears resume.

```bash
/usr/bin/python3 -I -s -B "$P/a/4.py" \
  --parts "$P/a/e/0" "$P/a/e/1" "$P/a/e/2" "$P/a/e/3" \
  --done "$DONE" --object "$OBJECT" \
  --config "$PREP/config.json" --receipt "$PREP/prepared/s1_receipt.json" \
  --data-receipt "$RUN/inputs/data_receipt.json" \
  --lineage SFT --step 100 --out "$P/a/export.json" --prep-tar "$P/a/e/4" \
  --base-inputs /project/community/jjyeung/b01ec87a6f29b/a/1.json \
  --inputs-out "$P/a/1.json"
```

The selected types are exactly `camera_displacement, camera_rotation, camera_movement_direction`, in that order. The observed member directory comes from the tar, not the object name or step label. `EXPORT_SCHEMA.md` documents every field.

Run the metadata check for one GPU and four hours. A pass writes `2.json` with `passed:true`, `scope:0`, `gpus:1`, `time:"04:00:00"`, the new package plan, the exact raw input hash, and the package hash. It verifies metadata and staged part sizes; it does not claim to have hashed the large archives or restored the model.

```bash
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:00:00
/usr/bin/python3 -I -s -B - <<'PY'
import json
from pathlib import Path
c=json.loads(Path('2.json').read_text())
assert c['passed'] is True and c['scope']==0 and c['gpus']==1 and c['time']=='04:00:00'
assert c['plan']==json.loads(Path('0.json').read_text())['plan_sha256']
print(json.dumps(c,indent=2))
PY
```

For a full empty-root CPU check before the read, use the actual packaged environment on an allocated compute node. This stages the same inputs and runs the same preparation entry point as the read. It consumes substantial project-disk IO; run it once, separately from other staging. `a/c/CPU.json` records the plan, inputs, payload, job-private storage proof, and `READY` hashes. Its `passed:true` establishes restore success, not GPU decoding or parity accuracy. No synthetic receipt can satisfy this check.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" --results "$P/a/c"
```

The evaluator's unchanged submit helper requests `--partition=general --gres=gpu:1`; it has no GPU-model selector. To guarantee H100 placement without changing that helper, proceed only if every GPU resource in `general` is typed H100. This explicit precondition avoids claiming that generic `gpu:1` selects H100 on a mixed partition. If the check fails or GRES names omit the model, stop and obtain a confirmed placement rule; this package does not add one.

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PY'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu, 'No typed GPU evidence for general'
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu), \
       'General is not proved to contain only typed H100 GPUs; stop'
print('General GPU resources are all typed H100')
PY
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 04:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

The read allocation stages into its own `/tmp` mount. The batch also creates `/tmp/a<job-id><package-token>` with an exclusive `mkdir`. `storage_proof` requires the mount's kernel identity to include `job_tmp/<job-id>`. Bubblewrap maps only that allocation's `sj` subtree onto `/scratch/jjyeung`. Two allocations therefore see the same logical root while using different physical storage; a duplicate bootstrap within one allocation refuses.

Four hours allows the measured 7,322 seconds of H1-0 camera work, the unchanged 1,800-second stop margin, and about 88 minutes for staging, preparation, and variation. The budget remains one GPU, four hours, below the unchanged five GPU-hour cap. No automatic retry follows a partial read.

Fetch after the allocation returns. Check status at most once per minute. The return token belongs to this package and appends the job ID as eight hexadecimal digits.

```bash
JOB=$(<"$P/a/8.txt")
RETURN=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PY'
import sys
print('bf94a7976a7e9'+format(int(sys.argv[1]),'08x'))
PY
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RETURN" --out "$P/a/f"
/usr/bin/python3 -I -s -B - "$P/a/f/0.tgz" <<'PY'
import csv,io,json,sys,tarfile
with tarfile.open(sys.argv[1]) as t:
    summary=json.load(t.extractfile('SUMMARY.json'))
    cards=json.load(t.extractfile('metadata/CARDS.json'))
    assert summary['complete'] is True and summary['completed']==summary['expected']==1050
    assert len(cards['visible'])==1
    rows=list(csv.reader(io.StringIO(cards['query'])))
    assert rows[1:] and all('H100' in row[1] for row in rows[1:])
    print(json.dumps(summary,indent=2))
PY
```

Score the complete three-type prefix with the byte-identical supplied `submerge.py`. The node helper restores the same export in a fresh job-private namespace from the same inputs, extracts the fetched return, and invokes `submerge.py JOURNALS OUTPUT 3` in the pinned environment. The logical package path remains `/scratch/jjyeung/b01ec87a6f29b/p`, but it contains the new package bytes. `submerge.py` checks the new evaluator hash against every journal; the wrapper additionally requires the scored export hash, lineage, and step to equal the returned binding before publishing scores.

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --return-tar "$P/a/f/0.tgz" --submerge "$P/a/6.py" --results "$P/a/s"
```

Read `a/s/curve.json`, `a/s/report.md`, and `a/s/items.jsonl`. The unchanged statistics use room bootstrap, 10,000 draws, seed `20261115`, and 95% intervals. Scoring refuses incomplete camera coverage. Keep the pin file and inputs unchanged from check through scoring. A different export requires new inputs and a new metadata check, even when using this same package.

Lineage: every current leg, including repair leg R1, is an SFT leg; fill its exports with `--lineage SFT --step <optimizer step>`. `RL` is reserved for RL legs, which do not exist yet.

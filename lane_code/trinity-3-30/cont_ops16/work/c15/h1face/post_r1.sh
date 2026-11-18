#!/bin/bash
# post-fetch for an R1 direct read: STEP=<100|200|...> TOK=<token>; manifests, export receipt placement, pooled rule v3, r0cmp vs 544
set -euo pipefail; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1; PY=/scratch/jjyeung/envs/p1cpu/bin/python
R1_READ=$PWD/kit/build/${TOK:?}; S=${STEP:?}
POOLED=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule
test -e "$R1_READ/R0-dev_MANIFEST.json" || "$PY" -B "$POOLED/build_manifest.py" kit "$R1_READ" R0-dev "$R1_READ/R0-dev_MANIFEST.json"
test -e "$R1_READ/dev-S1_MANIFEST.json" || "$PY" -B "$POOLED/build_manifest.py" kit "$R1_READ" dev-S1 "$R1_READ/dev-S1_MANIFEST.json"
test -e "$R1_READ/runs/673bc60f/m$S/artifact.json" || "$PY" -B - "$R1_READ" "$S" <<'PY'
import hashlib, json, sys
from pathlib import Path
build = Path(sys.argv[1]); step = int(sys.argv[2])
x = build/'fetched/x'
spec = json.loads((x/'SPEC.json').read_text())
raw = (x/'metadata/EXPORT_ARTIFACT.json').read_bytes()
assert spec['export_binding']['run'] == '673bc60f' and spec['step'] == step
assert hashlib.sha256(raw).hexdigest() == spec['artifact']['sha256']
assert json.loads(raw)['step'] == step
out = build/f'runs/673bc60f/m{step}/artifact.json'
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('xb') as stream:
    stream.write(raw)
PY
if [ "$S" = 100 ]; then CAL="--calibration --step 200"; else CAL="--step $S"; fi
"$PY" -B "$POOLED/pooled_harm_rule_v3.py" $CAL \
  --read "$R1_READ/fetched/x/ITEMS.jsonl" \
  --manifest-s1 "$R1_READ/dev-S1_MANIFEST.json" \
  --manifest-r0 "$R1_READ/R0-dev_MANIFEST.json" \
  --export-receipt "$R1_READ/runs/673bc60f/m$S/artifact.json" \
  --ledger "$POOLED/READ_LEDGER.jsonl" \
  --output "$R1_READ/R1_${S}_POOLED.json" 2>&1 | tee "$R1_READ/R1_${S}_POOLED.txt"
"$PY" -B r0cmp.py --b kit/build/adff67f7ae9/fetched/x --a R1m$S="$R1_READ/fetched/x" --output "$R1_READ/R0CMP_m$S.json" 2>&1 | tee "$R1_READ/R0CMP_m$S.txt"

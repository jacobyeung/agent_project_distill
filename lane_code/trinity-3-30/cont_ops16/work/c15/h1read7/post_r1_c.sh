#!/bin/bash
# cont_ops17 copy for run 6ed2c7aa. post-fetch for an R1 direct read: STEP=<100|200|...> TOK=<token>; manifests, export receipt placement, pooled rule v3, r0cmp vs 544
set -euo pipefail; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read7
export PYTHONDONTWRITEBYTECODE=1; PY=/scratch/jjyeung/envs/p1cpu/bin/python
R1_READ=$PWD/kit/build/${TOK:?}; S=${STEP:?}
POOLED=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule
test -e "$R1_READ/R0-dev_MANIFEST.json" || "$PY" -B "$POOLED/build_manifest.py" kit "$R1_READ" R0-dev "$R1_READ/R0-dev_MANIFEST.json"
test -e "$R1_READ/dev-S1_MANIFEST.json" || "$PY" -B "$POOLED/build_manifest.py" kit "$R1_READ" dev-S1 "$R1_READ/dev-S1_MANIFEST.json"
test -e "$R1_READ/runs/6ed2c7aa/m$S/artifact.json" || "$PY" -B - "$R1_READ" "$S" <<'PY'
import hashlib, json, sys
from pathlib import Path
build = Path(sys.argv[1]); step = int(sys.argv[2])
x = build/'fetched/x'
spec = json.loads((x/'SPEC.json').read_text())
raw = (x/'metadata/EXPORT_ARTIFACT.json').read_bytes()
assert spec['export_binding']['run'] == '6ed2c7aa' and spec['step'] == step
assert hashlib.sha256(raw).hexdigest() == spec['artifact']['sha256']
assert json.loads(raw)['step'] == step
out = build/f'runs/6ed2c7aa/m{step}/artifact.json'
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('xb') as stream:
    stream.write(raw)
PY
# Amendment C1 tool (pins run by step: 673bc60f <=200, 6ed2c7aa 400/600/800); decision mode only once the orchestrator's registration exists
TOOL=/scratch/jjyeung/orch_n30/cont_ops17/pooled_c1/pooled_harm_rule_v3_c1.py
test -s "$POOLED/REGISTERED_POOLED_RULE_R1_AMENDMENT_C1.md" || { echo "REFUSED: amendment C1 not registered; no step-$S output is opened"; exit 7; }
CAL="--step $S"
"$PY" -B "$TOOL" $CAL \
  --read "$R1_READ/fetched/x/ITEMS.jsonl" \
  --manifest-s1 "$R1_READ/dev-S1_MANIFEST.json" \
  --manifest-r0 "$R1_READ/R0-dev_MANIFEST.json" \
  --export-receipt "$R1_READ/runs/6ed2c7aa/m$S/artifact.json" \
  --ledger "$POOLED/READ_LEDGER.jsonl" \
  --output "$R1_READ/R1_${S}_POOLED.json" 2>&1 | tee "$R1_READ/R1_${S}_POOLED.txt"
"$PY" -B r0cmp.py --b /scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/x --a R1m$S="$R1_READ/fetched/x" --output "$R1_READ/R0CMP_m$S.json" 2>&1 | tee "$R1_READ/R0CMP_m$S.txt"

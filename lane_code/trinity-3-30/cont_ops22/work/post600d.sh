#!/bin/bash
# cont_ops22 post600d: DIAGNOSTIC post-processing of the step-600 direct read (TOK=a136f924ab1), forecast for N, never a leg-R1 decision.
# = cont_ops/work/h1read7/post400.sh + post_r1_c.sh + cont_ops19 post600_extra.sh, with: build copy in /dev/shm (no file >5 MB on 3-30), pooled tool WITHOUT --ledger.
set -uo pipefail; K=/scratch/jjyeung/orch_n30/cont_ops/work/h1read7; cd $K
export PYTHONDONTWRITEBYTECODE=1 PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$K/kit/launcher/orchard_launcher.py OMP_NUM_THREADS=1
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
T=${TOK:-a136f924ab1}; S=600; SRC=$K/kit/build/$T; B=/dev/shm/c22/build/$T; LOG=/scratch/jjyeung/orch_n30/cont_ops22/work/post600_$T.log
POOLED=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule; C19=/scratch/jjyeung/orch_n30/cont_ops19/work; C=/scratch/jjyeung/orch_n30/cont_ops/work
mkdir -p /dev/shm/c22/build; test -d $B || cp -a $SRC $B
{
echo "== $(date -u +%TZ) fetch"; test -s $B/fetched/result.tar.gz || "$PY" -B "$L" fetch --destination "$B" || { echo FETCH_FAILED; exit 2; }
sha256sum $B/fetched/result.tar.gz; cat $B/fetched/EXIT.json; echo
echo "== unpack"; test -d $B/fetched/x || "$PY" -B tools/unpack_return.py --destination "$B" || { echo UNPACK_FAILED; exit 3; }
echo "== pool move"; timeout 300 bash $A_TRANSPORT "T=$T bash -s" < o_mvpool112.sh
for f in /scratch/jjyeung/orch_n30/cont_ops17/pooled_c1/pooled_harm_rule_v3_c1.py:45f9999fedf35365d148ba66e5a4a0fd7a57036bd6ca14e7c5153478ed8d40f3 /scratch/jjyeung/orch_n30/cont_ops17/pooled_c1/count_runaways.py:642a5850d55afcd829eea37ee4a8639025f93a2b578047e0d88b58815cf1b615; do test "$(sha256sum ${f%%:*} | cut -d' ' -f1)" = "${f#*:}" || { echo "PIN_DIFFERS ${f%%:*}"; exit 5; }; done
echo "== manifests + export receipt"
test -e "$B/R0-dev_MANIFEST.json" || "$PY" -B "$POOLED/build_manifest.py" kit "$B" R0-dev "$B/R0-dev_MANIFEST.json"
test -e "$B/dev-S1_MANIFEST.json" || "$PY" -B "$POOLED/build_manifest.py" kit "$B" dev-S1 "$B/dev-S1_MANIFEST.json"
test -e "$B/runs/6ed2c7aa/m$S/artifact.json" || "$PY" -B - "$B" "$S" <<'PY'
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
echo "== pooled tool, DIAGNOSTIC (no ledger), step $S levels"
"$PY" -B /scratch/jjyeung/orch_n30/cont_ops17/pooled_c1/pooled_harm_rule_v3_c1.py --step $S --read "$B/fetched/x/ITEMS.jsonl" --manifest-s1 "$B/dev-S1_MANIFEST.json" --manifest-r0 "$B/R0-dev_MANIFEST.json" --export-receipt "$B/runs/6ed2c7aa/m$S/artifact.json" --output "$B/R1_${S}_POOLED_DIAG.json" 2>&1 | tee "$B/R1_${S}_POOLED_DIAG.txt"
echo "== paired vs 400 (pooled tool on the 400 read, no ledger, for the same items)"
"$PY" -B "$K/r0cmp.py" --b $C/h1read/kit/build/adff67f7ae9/fetched/x --a R1m400=$K/kit/build/a59a7bff4c4/fetched/x R1m$S="$B/fetched/x" --output "$B/R0CMP_m$S.json" 2>&1 | tee "$B/R0CMP_m$S.txt"
echo "== runaways"; "$PY" -B /scratch/jjyeung/orch_n30/cont_ops17/pooled_c1/count_runaways.py --x $B/fetched/x --output $B/RUNAWAYS_m$S.json
echo "== DERIVED (calibration)"; "$PY" -B ../cfix/derived_v3.py --step $S --calibration --read $B/fetched/x/ITEMS.jsonl --manifest-s1 $B/dev-S1_MANIFEST.json --manifest-r0 $B/R0-dev_MANIFEST.json --x $B/fetched/x --export-receipt $B/runs/6ed2c7aa/m$S/artifact.json --output $B/R1_${S}_DERIVED.json
echo "== split"; "$PY" -B ../split/split.py --x $B/fetched/x --label R1m$S --out $B/SPLIT_R1m$S.json
echo "== relative size"; "$PY" -B ../split/relsize.py --x $B/fetched/x | tee $B/RELSIZE_m$S.json
echo "== relative count dev-S1 (200, 400, 600)"; python3 $C19/relcount.py $C/h1read/kit/build/a8102c3207b/fetched/x/ITEMS.jsonl $K/kit/build/a59a7bff4c4/fetched/x/ITEMS.jsonl $B/fetched/x/ITEMS.jsonl
echo "== counting split 2/3/4/5+ (600)"; "$PY" -B $C19/split5.py --x $B/fetched/x --label R1m600 --out $B/SPLIT5_R1m600.json | grep counting
echo "== counting split (400 reference)"; grep -h counting $C19/SPLIT5_R1m400.txt 2>/dev/null || "$PY" -B $C19/split5.py --x $K/kit/build/a59a7bff4c4/fetched/x --label R1m400 --out /dev/null | grep counting
echo "== copy small outputs back"; mkdir -p /scratch/jjyeung/orch_n30/cont_ops22/work/post600_$T; for f in $B/*.json $B/*.txt; do [ $(stat -c %s $f) -lt 5000000 ] && cp $f /scratch/jjyeung/orch_n30/cont_ops22/work/post600_$T/; done
echo "== done $(date -u +%TZ)"
} 2>&1 | tee -a $LOG

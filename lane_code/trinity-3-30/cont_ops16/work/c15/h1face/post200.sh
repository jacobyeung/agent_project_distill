#!/bin/bash
# cont_ops16 rebuild of post200: TOK=<token> STEP=<200>; fetch, unpack, pool move, registered rule (decision, ledger) via post_r1.sh,
# DERIVED rule (amendment 1108Z), counting split, relative size; log kit/build/<tok>/POST200.log
set -uo pipefail; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1 PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
T=${TOK:?}; S=${STEP:-200}; B=$PWD/kit/build/$T; LOG=$B/POST200.log
{
echo "== $(date -u +%TZ) fetch"; test -s $B/fetched/result.tar.gz || "$PY" -B "$L" fetch --destination "$B" || { echo FETCH_FAILED; exit 2; }
sha256sum $B/fetched/result.tar.gz; cat $B/fetched/EXIT.json; echo
echo "== unpack"; test -d $B/fetched/x || "$PY" -B tools/unpack_return.py --destination "$B" || { echo UNPACK_FAILED; exit 3; }
echo "== pool move"; timeout 300 bash $A_TRANSPORT "T=$T bash -s" < o_mvpool112.sh
echo "== registered rule (decision mode, ledger)"; STEP=$S TOK=$T bash post_r1.sh
echo "== DERIVED rule (amendment 1108Z)"; "$PY" -B ../cfix/derived_v3.py --step $S --read $B/fetched/x/ITEMS.jsonl --manifest-s1 $B/dev-S1_MANIFEST.json --manifest-r0 $B/R0-dev_MANIFEST.json --x $B/fetched/x --export-receipt $B/runs/673bc60f/m$S/artifact.json --output $B/R1_${S}_DERIVED.json
echo "== split"; "$PY" -B ../split/split.py --x $B/fetched/x --label R1m$S --out $B/SPLIT_R1m$S.json
echo "== relative size"; "$PY" -B ../split/relsize.py --x $B/fetched/x | tee $B/RELSIZE_m$S.json
echo "== artifact"; sha256sum $B/runs/673bc60f/m$S/artifact.json
echo "== done $(date -u +%TZ)"
} 2>&1 | tee -a $LOG

#!/bin/bash
# Review-gate check of vehicle N's launch job, end to end (ORCH RULING 0211Z items 4-5). Run on trinity-3-30.
# Usage: bash run_gate.sh <slurm job id> <fresh local out dir under /scratch/jjyeung/orch_n30/<your lane>/>
# 1. Orchard (one ossh call over the existing master; stops on any host-key line): tar of X/o/<job>/live and
#    X/o/<job>_gate (jn6 copy; or the n_ops10 srun fallback) -> <out>/x/.
# 2. trinity-1-18 (one tssh call): v.json + identity.txt -> W/w24z14/work/gate_<job>_<stamp>/in, admit_test.sh there
#    (it may write only under W/w24z14), ADMIT.json back -> <out>/ADMIT.json.
# 3. gate.py on <out>/x --admit <out>/ADMIT.json -> <out>/gate.out; last line GATE ALL PASS|FAIL; exit 0 only on PASS.
set -uo pipefail
JOB=${1:?job id}; OUT=${2:?out dir}
[[ $JOB =~ ^[0-9]+$ ]] || { echo "bad job id"; exit 2; }
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
X=/project/community/jjyeung/okh7/x_22c714e1
mkdir -p "$OUT" && [ -z "$(ls -A "$OUT")" ] || { echo "out dir must be new and empty"; exit 2; }
cd "$OUT"
cat > o_fetch.sh <<EOF
cd $X/o < /dev/null || exit 3
ls -la $JOB/live ${JOB}_gate < /dev/null 1>&2
du -sb $JOB/live ${JOB}_gate < /dev/null 1>&2
tar cf - $JOB/live \$( [ -d ${JOB}_gate ] && echo ${JOB}_gate ) < /dev/null | base64 -w0
EOF
ssh -o ControlPath=/tmp/cm-n30-orchard-%r -O check orchard 2>/dev/null || echo "NOTE no live Orchard master; ossh will open a new connection"
timeout 300 bash $B/tools/ossh.sh 'bash -s' < o_fetch.sh > x.tar.b64 2> o_fetch.err; rc=$?
if grep -qi 'host identification\|host key\|man-in-the-middle' o_fetch.err; then
  echo "HOST-KEY LINE on Orchard: stop all Orchard calls and post a BLOCKER (ANSWER 0222Z item 3):"; grep -i 'host' o_fetch.err; exit 4; fi
[ $rc = 0 ] || { echo "Orchard fetch rc $rc (one failure: wait 2 min, retry once; a second is a BLOCKER)"; cat o_fetch.err; exit 5; }
mkdir x && base64 -d x.tar.b64 > x.tar && tar xf x.tar -C x || { echo "fetch decode failed"; exit 5; }
sha256sum x.tar; cat o_fetch.err
V=x/$JOB/live/v.json; I=x/$JOB/live/identity.txt
if [ -f "$V" ] && [ -f "$I" ]; then
  ST=$(date -u +%Y%m%dT%H%M%SZ); D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/work/gate_${JOB}_$ST
  { echo "set -u; mkdir -p $D/in"
    echo "base64 -d > $D/in/v.json <<'B64'"; base64 "$V"; echo "B64"
    echo "base64 -d > $D/in/identity.txt <<'B64'"; base64 "$I"; echo "B64"
    echo "cd $D && sha256sum in/v.json in/identity.txt 1>&2 < /dev/null"
    echo "timeout 900 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/out/admit_test.sh $D/in/v.json $D/admit > $D/admit.stdout 2>&1 < /dev/null; echo admit_rc=\$? 1>&2"
    echo "tail -3 $D/admit.stdout 1>&2; base64 -w0 $D/admit/ADMIT.json < /dev/null"; } > t_admit.sh
  bash $B/tools/tssh.sh trinity-1-18 'bash -s' < t_admit.sh > ADMIT.json.b64 2> t_admit.err
  base64 -d ADMIT.json.b64 > ADMIT.json 2>/dev/null; cat t_admit.err; echo "admit test dir on trinity-1-18: $D"
else
  echo "v.json or identity.txt absent on X: admit test not run (the admit point fails)"
fi
A=(); [ -s ADMIT.json ] && A=(--admit ADMIT.json)
python3 -I "$HERE/gate.py" x "${A[@]}" > gate.out 2>&1; grc=$?
sha256sum "$HERE/gate.py" gate.out
grep -v '^FILE .*ABSENT' gate.out
exit $grc

#!/bin/bash
# Review-gate check of vehicle N's launch job, end to end (ORCH RULING 0211Z items 4-5). Run on trinity-3-30.
# Usage: bash run_gate.sh <slurm job id> <fresh local out dir under /scratch/jjyeung/orch_n30/<your lane>/> [--local DIR]
#   --local DIR: skip Orchard; DIR on trinity-3-30 holds the same files (any layout; the prepared receipt in a folder named b,
#   gate or *_gate), e.g. the srun --overlap stream of ORCH ORDER 1055Z item 1.
# 1. Orchard (one ossh call over the existing master; stops on any host-key line): tar of the named gate files in X/o/<job>/live
#    (never the whole dir: the copier keeps up to 50 MB of logs there) and
#    X/o/<job>_gate (jn6 copy; or the n_ops10 srun fallback) -> <out>/x/.
# 2. trinity-1-18 (one tssh call): v.json + identity.txt -> W/w24z14/work/gate_<job>_<stamp>/in, admit_test.sh there
#    (it may write only under W/w24z14), ADMIT.json back -> <out>/ADMIT.json.
# 3. gate.py on <out>/x --admit <out>/ADMIT.json -> <out>/gate.out; last line GATE ALL PASS|FAIL; exit 0 only on PASS.
# 4. spell.py on <out>/x -> <out>/spell.out: the job-folder spelling in frames.json / request.json (info only; exit code unchanged).
set -uo pipefail
JOB=${1:?job id}; OUT=${2:?out dir}
[[ $JOB =~ ^[0-9]+$ ]] || { echo "bad job id"; exit 2; }
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
X=/project/community/jjyeung/okh7/x_22c714e1
mkdir -p "$OUT" && [ -z "$(ls -A "$OUT")" ] || { echo "out dir must be new and empty"; exit 2; }
cd "$OUT"
LOCAL=""; [ "${3:-}" = "--local" ] && LOCAL=${4:?--local needs a folder}
if [ -n "$LOCAL" ]; then
  mkdir x && cp -r "$LOCAL"/. x/ && echo "NOTE local evidence from $LOCAL (no Orchard read)"; find x -type f | sort | xargs sha256sum > x_local.sha256
else
cat > o_fetch.sh <<EOF
cd $X/o < /dev/null || exit 3
ls -la ${JOB}_gate < /dev/null 1>&2
L=""; for f in v.json identity.txt WAITING_REVIEW.json e0.json e1.json e2.json e3.json c0.json c1.json c2.json c3.json c4.json s2.json s1.json s4.json h0.json; do [ -f $JOB/live/\$f ] && L="\$L $JOB/live/\$f"; done
G=""; [ -d ${JOB}_gate ] && G=${JOB}_gate
[ -z "\$L\$G" ] || du -cb \$L \$G < /dev/null 2>&1 | tail -1 1>&2
if [ -n "\$L\$G" ]; then tar cf - \$L \$G < /dev/null | base64 -w0; fi
EOF
ssh -o ControlPath=/tmp/cm-n30-orchard-%r -O check orchard 2>/dev/null || echo "NOTE no live Orchard master; ossh will open a new connection"
timeout 300 bash $B/tools/ossh.sh 'bash -s' < o_fetch.sh > x.tar.b64 2> o_fetch.err; rc=$?
if grep -qi 'host identification\|host key\|man-in-the-middle' o_fetch.err; then
  echo "HOST-KEY LINE on Orchard: stop all Orchard calls and post a BLOCKER (ANSWER 0222Z item 3):"; grep -i 'host' o_fetch.err; exit 4; fi
[ $rc = 0 ] || { echo "Orchard fetch rc $rc (one failure: wait 2 min, retry once; a second is a BLOCKER)"; cat o_fetch.err; exit 5; }
mkdir x; if [ -s x.tar.b64 ]; then base64 -d x.tar.b64 > x.tar && tar xf x.tar -C x || { echo "fetch decode failed"; exit 5; }; else echo "NOTE no gate file on X for job $JOB"; : > x.tar; fi
[ $(stat -c %s x.tar) -lt 20000000 ] || echo "NOTE fetch above 20 MB: next time register it with the IO governor"
sha256sum x.tar; cat o_fetch.err
fi
V=$(find x -name v.json -type f | head -1); I=$(find x -name identity.txt -type f | head -1)
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
# ORCH ANSWER 1928Z item 4: which name of the job folder frames.json and request.json carry (informational, not a verdict).
python3 -I "$HERE/spell.py" x > spell.out 2>&1; cat spell.out
exit $grc

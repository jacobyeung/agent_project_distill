#!/bin/bash
# Builds the Orchard scripts of RUN.md from fix15/rh (re-run after any change to rh/).
set -eu
F=/scratch/jjyeung/orch_n30/tree_rebuild28/work/fix15; cd "$F"
J=${1:-174246}
SUMS=$(cd "$F" && sha256sum rh/* | cut -c1-12 | tr '\n' ' ')
{
cat <<HDR
export TZ=UTC; date -u +%TZ
# fix15 rehearsal start for job $J: ship rh/ (sha256 prefixes: $SUMS) to the node scratch, start the driver
# in its own srun --overlap step (CPU guards first, then the GPUs), first status after 40 s.
squeue -j $J -h -o '%T|%M|%N'
timeout 90 srun --overlap --jobid $J -N1 -n1 bash -c 'D=/tmp/a15_rh_$J; mkdir -p \$D && chmod 700 \$D && cd \$D && base64 -d | tar xzf - && echo "shipped: \$(sha256sum rh/* | cut -c1-12 | tr "\n" " ")"; ls -d \$D/run_* 2>/dev/null | tail -3' <<'B64'
HDR
tar czf - rh | base64
cat <<TAIL
B64
nohup setsid srun --overlap --jobid $J -N1 -n1 timeout -s TERM -k 20 870 bash /tmp/a15_rh_$J/rh/go.sh > /dev/null 2>&1 < /dev/null &
echo "started srun pid \$! at \$(date -u +%TZ)"
sleep 40
timeout 60 srun --overlap --jobid $J -N1 -n1 bash -c 'cat /tmp/a15_rh_$J/last/log/go.log 2>&1 | cut -c1-600 | tail -n 20'
date -u +%TZ
TAIL
} > s/o_start.sh
cat > s/o_poll.sh <<POLL
export TZ=UTC; date -u +%TZ
timeout 60 srun --overlap --jobid $J -N1 -n1 bash -c 'L=/tmp/a15_rh_$J/last/log; tail -n 14 \$L/go.log | cut -c1-500; echo "== stages"; for f in \$L/ev_rank*.jsonl; do echo "\$(basename \$f) \$(tail -n 1 \$f | cut -c1-260)"; done; grep -h "\"kind\": \"\(STEP\|ERROR\)\"" \$L/ev_rank*.jsonl 2>/dev/null | cut -c1-700 | tail -n 10; echo "== gpu"; tail -n 4 \$L/smi.csv 2>/dev/null; echo "== t.raw tail"; tail -n 6 \$L/t.raw.log 2>/dev/null | cut -c1-300; [ -f /tmp/a15_rh_$J/last/summary.json ] && cat \$L/sum.out | cut -c1-5000'
POLL
cat > s/o_stop.sh <<STOP
export TZ=UTC; date -u +%TZ
timeout 90 srun --overlap --jobid $J -N1 -n1 bash /tmp/a15_rh_$J/rh/stop.sh
STOP
cat > s/o_pull.sh <<PULL
export TZ=UTC; date -u +%TZ
timeout 80 srun --overlap --jobid $J -N1 -n1 bash -c 'R=\$(readlink -f /tmp/a15_rh_$J/last); cd \$R && tail -c 3000000 log/t.raw.log > log/t.tail.log; tar czf - summary.json log/go.log log/accept.log log/ev_rank0.jsonl log/ev_rank1.jsonl log/ev_rank2.jsonl log/ev_rank3.jsonl log/smi.csv log/t.tail.log log/t.rc log/proof.txt log/job_before.txt log/job_after.txt log/env.txt log/bwrap_args.txt w/top/p/q/r/smoke 2>/dev/null | head -c 15000000 | base64 -w 76'
PULL
echo "built s/o_start.sh ($(wc -c < s/o_start.sh) B), s/o_poll.sh, s/o_stop.sh, s/o_pull.sh for job $J"

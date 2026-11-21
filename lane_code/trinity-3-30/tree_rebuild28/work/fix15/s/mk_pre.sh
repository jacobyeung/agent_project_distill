#!/bin/bash
set -eu; cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix15; J=174246
{
echo 'export TZ=UTC; date -u +%TZ'
echo "squeue -j $J -h -o '%T|%M|%N'"
echo "timeout 150 srun --overlap --jobid $J -N1 -n1 bash -c 'D=/tmp/a15_rh_$J; Q=/tmp/q_22c714e1_$J; mkdir -p \$D && chmod 700 \$D && cd \$D && base64 -d | tar xzf - && echo \"shipped: \$(sha256sum rh/* | cut -c1-12 | tr \"\\n\" \" \")\"; echo \"== p\"; ls -la \$Q/p | cut -c1-120; echo \"== p/q\"; ls -la \$Q/p/q | cut -c1-120 | head -70; echo \"== live\"; ls -la /project/community/jjyeung/okh7/x_22c714e1/o/$J/live 2>&1 | cut -c1-120 | head; ls /project/community/jjyeung/okh7/x_22c714e1/n_r 2>&1 | head -3; echo \"== pre\"; nice -n 10 timeout 100 bash \$D/rh/pre.sh; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr \"\\n\" \";\"; echo; tail -n 3 \$Q/$J.steps | cut -c1-160' <<'B64'"
tar czf - rh | base64
echo 'B64'
echo 'date -u +%TZ'
} > s/o_pre.sh
echo "built s/o_pre.sh $(wc -c < s/o_pre.sh) B"

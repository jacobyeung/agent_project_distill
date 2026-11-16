#!/bin/bash
# After k1_ops7_ownret ends: verify, extract, census, launch convert in tmux k1conv.
set -euo pipefail
W=/scratch/jjyeung/orch_n30/k1_ops3/work; F=$W/own7/ad2472b1be07d4193.result.tar.gz
S=/data3/jjyeung/orch_n13_20261026/io_governor/streams/k1_ops7_ownret.json
[ -f $S ] && mv $S ${S%.json}.done.$(date +%s)
echo "09699e6755b0e3ae5d2b624d54ac7af4ad9bb7a0ba65829de7eb2b87fe8fbb98  $F" | sha256sum -c --strict -
[ $(stat -c %s $F) = 97853329 ]
D=/scratch/jjyeung/k1/own_170235; mkdir $D; tar xzf $F -C $D
echo "PHASE_COMPLETE: $(ls $D/native/probe/*/PHASE_COMPLETE.json | wc -l)"
cd $W/own7/diag && CUDA_VISIBLE_DEVICES='' /scratch/jjyeung/envs/sam3_scipy_ovl/bin/python -B guard_census.py $D/native/probe full_guard.json | head -1
tmux new-session -d -s k1conv "bash $W/kc_guard_brief/convert7.guard.sh $D/native/probe /scratch/jjyeung/k1/run_convert_1 > /scratch/jjyeung/k1/CONVERT1.log 2>&1"
echo "convert launched $(date -u +%FT%TZ)"

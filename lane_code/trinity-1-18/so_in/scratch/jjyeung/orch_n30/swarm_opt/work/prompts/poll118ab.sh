#!/bin/bash
L=/scratch/jjyeung/orch_n30/so_launch
if ! tmux has-session -t =so_launch_gloo 2>/dev/null && [[ ! -f $L/work/port21_gloo_by_swarm_opt.txt ]]; then
 tmux new-session -d -s so_launch_gloo "cd $L && SO_NO_LOCAL_SOCKETS=0 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false nice -n 10 taskset -c 8-15 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $L/work/run_native_regression.py $L/work/port21/recommended > $L/work/port21_gloo_by_swarm_opt.txt 2>&1; echo EXIT=\$? >> $L/work/port21_gloo_by_swarm_opt.txt"; echo started so_launch_gloo; fi
W=/scratch/jjyeung/orch_n30/so_git/work/realgit3_by_swarm_opt; for f in $W/run_*.txt; do echo "== $f"; grep -E "^Ran|^OK|FAILED|rc=|Error|error:" $f | tail -6 | cut -c1-250; done

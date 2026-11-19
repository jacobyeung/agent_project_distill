#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
L=/scratch/jjyeung/orch_n30/so_launch
if ! tmux has-session -t =so_launch_gloo 2>/dev/null && [[ ! -f $L/work/port21_gloo3_by_swarm_opt.txt ]]; then
 mkdir -p $L/work/tmp_gloo3 $L/work/lane_test_output3
 tmux new-session -d -s so_launch_gloo "cd $L && { [ -f work/env.sh ] && source work/env.sh; true; } && export TMPDIR=$L/work/tmp_gloo3 LANE_TEST_OUTPUT=$L/work/lane_test_output3 SO_NO_LOCAL_SOCKETS=0 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false && nice -n 10 taskset -c 8-15 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $L/work/run_native_regression.py $L/work/port21/recommended > $L/work/port21_gloo3_by_swarm_opt.txt 2>&1; echo EXIT=\$? >> $L/work/port21_gloo3_by_swarm_opt.txt"; echo started so_launch_gloo v3; fi
[[ -d /scratch/jjyeung/orch_n30/so_cr_step3 ]] || bash $P/cursor_start.sh so_cr_step3 $P/cr_step3.md
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
echo "modep2: $(head -1 /scratch/jjyeung/orch_n30/so_cr_modep2/REVIEW_VERDICT.md 2>/dev/null)"
for d in /scratch/jjyeung/orch_n30/so_step/out/patches_b21 /scratch/jjyeung/orch_n30/so_modep/out/patches; do ls $d; sha256sum $d/*.diff | cut -c1-16,65-200; done
uptime

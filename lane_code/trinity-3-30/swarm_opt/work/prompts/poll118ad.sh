#!/bin/bash
L=/scratch/jjyeung/orch_n30/so_launch; S=/scratch/jjyeung/orch_n30/so_step
if ! tmux has-session -t =so_launch_gloo 2>/dev/null && [[ ! -f $L/work/port21_gloo2_by_swarm_opt.txt ]]; then
 mkdir -p $L/work/tmp_gloo2; ls $L/work/env.sh 2>/dev/null
 tmux new-session -d -s so_launch_gloo "cd $L && { [ -f work/env.sh ] && source work/env.sh; true; } && export TMPDIR=$L/work/tmp_gloo2 SO_NO_LOCAL_SOCKETS=0 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false && nice -n 10 taskset -c 8-15 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $L/work/run_native_regression.py $L/work/port21/recommended > $L/work/port21_gloo2_by_swarm_opt.txt 2>&1; echo EXIT=\$? >> $L/work/port21_gloo2_by_swarm_opt.txt"; echo started so_launch_gloo v2; fi
awk '/^## Coordinator command/{f=1} f&&/^```/{n++; if(n==2){exit}; next} f&&n==1{print}' $S/out/REPORT.md > $S/work/gloo_cmd_b21.sh; cat $S/work/gloo_cmd_b21.sh
OUT=$(grep -o '> *[^ ]*\.txt' $S/work/gloo_cmd_b21.sh | head -1 | tr -d '> '); echo "out=$OUT"
if [[ -s $S/work/gloo_cmd_b21.sh ]] && ! tmux has-session -t =so_step_gloo3 2>/dev/null && [[ ! -f $S/work/GLOO_B21_STARTED ]]; then date -u > $S/work/GLOO_B21_STARTED
  tmux new-session -d -s so_step_gloo3 "cd $S && bash work/gloo_cmd_b21.sh; echo EXIT=\$? >> $S/work/gloo_b21_exit.txt"; echo started so_step_gloo3; fi
uptime

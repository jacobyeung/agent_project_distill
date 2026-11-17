set -u
hostname -s; uptime; nproc; df -h /scratch | tail -1
H=/scratch/jjyeung/orch_n30/e3_geom/work/harness
ls -la $H; ls $H/out | head -30
ls /scratch/jjyeung/orch_n30/b04_e2ehook_sh 2>&1
ls -la /scratch/jjyeung/envs/planner_local_v1/bin/python /scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json /scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872 2>&1 | head
tmux ls 2>&1 | head
which tmux

set -eu
ROOT='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24i/copier_go_tests/before_signal_15/kit'
N='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24i/copier_go_tests/before_signal_15/node'
export SLURM_JOB_ID=41
source "$ROOT/b/pc.sh"
'/scratch/jjyeung/envs/p1cpu/bin/python' -B '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24i/copier_go_tests/before_signal_15/launcher.py' '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24i/copier_go_tests/before_signal_15/kit/b/u.py' "$N" &
TK_WORK_PID=$!
wait "$TK_WORK_PID"

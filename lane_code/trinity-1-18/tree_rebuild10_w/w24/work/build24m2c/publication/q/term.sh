set -euo pipefail
ROOT='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m2c/publication/q/kit'
N='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m2c/publication/q/node'
export SLURM_JOB_ID=96
source "$ROOT/b/ep.sh"
setsid sleep 30 &
TK_WORK_PID=$!
wait "$TK_WORK_PID"

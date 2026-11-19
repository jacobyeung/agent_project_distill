set -eu
ROOT='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/live_tests/term/kit'
N='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/live_tests/term/node'
export SLURM_JOB_ID=41
source "$ROOT/b/pc.sh"
printf ready > "$N/ready"
sleep 5 &
wait $!

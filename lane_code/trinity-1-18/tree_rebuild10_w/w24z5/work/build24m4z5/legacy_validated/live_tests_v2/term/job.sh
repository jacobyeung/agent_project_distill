set -eu
ROOT='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z5/work/build24m4z5/legacy_validated/live_tests_v2/term/kit'
N='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z5/work/build24m4z5/legacy_validated/live_tests_v2/term/node'
export SLURM_JOB_ID=41
source "$ROOT/b/pc.sh"
printf ready > "$N/ready"
sleep 5 &
wait $!

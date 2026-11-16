#!/bin/bash
# GRPO tests against the lane's tree copy. CPU only. Usage: bash rltests/run_grpo.sh [module ...]
export RLKIT_TREE=/scratch/jjyeung/orch_n30/review_rl/work/b09_rlkit/grpo_tree
exec bash /scratch/jjyeung/orch_n30/review_rl/work/b09_rlkit/rltests/run.sh ${@:-rltests.test_grpo}

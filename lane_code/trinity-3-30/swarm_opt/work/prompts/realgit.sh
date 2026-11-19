set -u
O=/scratch/jjyeung/orch_n30/so_git/work/patch_validation_oalqsw9w/owner
ls $O $O/tools | head -30
W=/scratch/jjyeung/orch_n30/so_git/work/realgit_by_swarm_opt; mkdir -p $W
cd $O && LCS_RUN_REAL_GIT_TESTS=1 LCS_REAL_GIT_WORK=$W LCS_PYTHON=/scratch/jjyeung/envs/p1cpu/bin/python timeout 600 bash tests/run_real_git_owner.sh > $W/run.txt 2>&1; echo "rc=$?" >> $W/run.txt
tail -40 $W/run.txt | cut -c1-300

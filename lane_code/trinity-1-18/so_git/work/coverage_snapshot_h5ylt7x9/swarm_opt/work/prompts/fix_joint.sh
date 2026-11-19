set -u
L=/scratch/jjyeung/orch_n30/so_step; T=$L/work/tree/tests/test_so_joint.py
sed -n 80,86p $T
if ! grep -q 'reshape(-1).view(torch.uint8)' $T; then
  cp $T $L/work/test_so_joint.py.before_swarm_opt
  sed -i '83s/source.detach().contiguous().view(torch.uint8)/source.detach().contiguous().reshape(-1).view(torch.uint8)/' $T
  (cd $L/work && diff -u test_so_joint.py.before_swarm_opt tree/tests/test_so_joint.py | sed -e '1s#^--- .*#--- a/tests/test_so_joint.py#' -e '2s#^+++ .*#+++ b/tests/test_so_joint.py#' > $L/out/patches/04_test_joint_hash_0dim.diff)
fi
sed -n 83p $T; cat $L/out/patches/04_test_joint_hash_0dim.diff
tmux has-session -t "=so_step_gloo2" 2>/dev/null || tmux new-session -d -s so_step_gloo2 "cd $L && export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false; date -u > work/full_suite_by_swarm_opt2.txt; nice -n 10 taskset -c 0-7 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint >> work/full_suite_by_swarm_opt2.txt 2>&1; echo EXIT=\$? >> work/full_suite_by_swarm_opt2.txt; date -u >> work/full_suite_by_swarm_opt2.txt"
echo started

cd /scratch/jjyeung/orch_n30/so_step
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/tree \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics tests.test_so_joint tests.test_so_review \
  > work/review1_full_suite_by_coordinator.txt 2>&1

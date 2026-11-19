cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  C1_CPU_PREFETCH=0 C1_DECODED_CACHE_MIB=0 C1_BATCH_METRICS=0 C1_CPU_PREFETCH_FALLBACK=0 \
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics \
  tests.test_so_joint tests.test_so_review tests.test_so_round2 tests.test_so_round3 \
  tests.test_gx_carrier.GXPTests.test_two_rank_gxp_first_batch_forward_backward \
  tests.test_gx_carrier.GXTests.test_two_rank_fsdp_replicas_checkpoint_and_exports \
  > work/round3_b21_gloo_by_coordinator.txt 2>&1
result=$?
printf '\nEXIT=%s\n' "$result" >> work/round3_b21_gloo_by_coordinator.txt
exit "$result"

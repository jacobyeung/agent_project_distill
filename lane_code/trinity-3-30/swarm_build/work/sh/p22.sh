R=/scratch/jjyeung/orch_n30; cd $R/sb_ktfix2
grep -n -E 'SHARED_GPU|GPU_GO|DA3_GO|reservation' code/runner.py scripts/run_A.sh scripts/gpu_environment.sh 2>/dev/null | cut -c1-220 | head -20

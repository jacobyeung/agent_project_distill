cd /scratch/jjyeung/orch_n30/so_syncfix
CHECK=$(< work/patchcheck_path.txt)
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
nice -n 10 env LCS_TEST_WORK="$PWD/work/final_py36" /usr/bin/python3 -I -s -B "$CHECK/tests/run_tests.py"
nice -n 10 env LCS_TEST_WORK="$PWD/work/final_py312" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$CHECK/tests/run_tests.py"

cd /scratch/jjyeung/orch_n30/native_r2/builds/01_c8
export PYTHONPATH=/scratch/jjyeung/orch_n30/native_r2/work/pyextra OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME=$PWD/work/cache HF_HOME=$PWD/work/hf TRITON_CACHE_DIR=$PWD/work/triton HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
nice -n 10 ionice -c3 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode ${1:-pilot} --dest $PWD/work/${2:-rh_pilot_01} > work/${2:-rh_pilot_01}.outer.log 2>&1
echo "exit $?" >> work/${2:-rh_pilot_01}.outer.log

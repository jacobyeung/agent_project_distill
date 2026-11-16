cd /scratch/jjyeung/orch_n30/native_r2/builds/02_c8r
export PYTHONPATH=/scratch/jjyeung/orch_n30/native_r2/work/np226:/scratch/jjyeung/orch_n30/native_r2/work/pyextra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export XDG_CACHE_HOME=$PWD/work/cache HF_HOME=$PWD/work/hf TRITON_CACHE_DIR=$PWD/work/triton HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
nice -n 10 ionice -c3 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode $1 --shards 1 --dest "$PWD/work/$2" > work/$2.log 2>&1
echo "exit $?" > work/$2.exit

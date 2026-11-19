cd /scratch/jjyeung/orch_n30/geo_k1/harness
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton" MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
mkdir -p tmp out_ref
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1_price.py --out out_ref --fits e3_FITS.json --shard $1/4 > ../logs/ref_$1.log 2>&1
echo EXIT $? >> ../logs/ref_$1.log

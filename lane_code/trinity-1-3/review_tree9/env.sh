R=/scratch/jjyeung/orch_n30/review_tree9; P=$R/pkg; T=$P/work/tree_r1
export TMPDIR=$R/tmp OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME=$R/tmp/cache HF_HOME=$R/tmp/hf TORCH_HOME=$R/tmp/torch HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 R2_FAST_CENSUS=1
export R2_FIXTURES=$P/fixtures R2_LANE_ROOT=$R/lane R2_PROOFS=$R/proofs PYTHONPATH=$T
PY="/scratch/jjyeung/envs/p1cpu/bin/python -s -B"

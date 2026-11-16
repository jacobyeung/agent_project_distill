# Source before running tests or examples: CPU only, the tree's CPU-gate interpreter and packages.
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4} MKL_NUM_THREADS=${MKL_NUM_THREADS:-4}
VLA_HEADS_ROOT=/scratch/jjyeung/orch_cd/vla_heads/work/vla_heads
VLA_TREE=${VLA_TREE:-/scratch/jjyeung/orch_cd/integ_v3/work/tree}
export XDG_CACHE_HOME=/scratch/jjyeung/orch_cd/vla_heads/work/cache TMPDIR=/scratch/jjyeung/orch_cd/vla_heads/work/tmp
mkdir -p "$XDG_CACHE_HOME" "$TMPDIR"
export PYTHONPATH="$VLA_HEADS_ROOT:$VLA_TREE:/scratch/jjyeung/orch_cd/integ_v3/work/numpy226:/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages:/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages"
export PATH="/scratch/jjyeung/envs/p1cpu/bin:$PATH"

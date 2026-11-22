#!/bin/bash
cd "/scratch/jjyeung/orch_n30/lever8/j1/kit"
export CUDA_VISIBLE_DEVICES= PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/xdg HF_HOME=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/hf TORCH_HOME=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/torch TRITON_CACHE_DIR=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/triton TORCHINDUCTOR_CACHE_DIR=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/inductor
export CUDA_CACHE_PATH=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/nv MPLCONFIGDIR=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/mpl TMPDIR=/scratch/jjyeung/orch_n30/lever8/j1/work/gpu_cache/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
timeout -k 30 3600 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B detect.py --device cpu --out /scratch/jjyeung/orch_n30/lever8/j1/work/dry_launch --hard-stop 3300 --captures scannet/scene0642_01 --anchor-limit 32

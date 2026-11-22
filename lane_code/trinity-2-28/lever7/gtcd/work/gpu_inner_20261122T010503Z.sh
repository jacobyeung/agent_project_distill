#!/bin/bash
cd "/scratch/jjyeung/orch_n30/lever7/gtcd/kit_ark"
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export XDG_CACHE_HOME=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/xdg HF_HOME=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/hf TORCH_HOME=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/torch TRITON_CACHE_DIR=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/triton TORCHINDUCTOR_CACHE_DIR=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/inductor
export CUDA_CACHE_PATH=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/nv MPLCONFIGDIR=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/mpl TMPDIR=/scratch/jjyeung/orch_n30/lever7/gtcd/work/gpu_cache/tmp HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
timeout -k 30 5400 /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -B track.py --device cuda --arms d --out /scratch/jjyeung/orch_n30/lever7/gtcd/out_ark/track --hard-stop 5280 --captures all --dense /scratch/jjyeung/orch_n30/lever7/gtcd/work/test_dense_ark/dense_ark/DENSE_D_ARK.json

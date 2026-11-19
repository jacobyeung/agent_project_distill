#!/usr/bin/env bash
export MDG_PYTHON=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
export PATH="/scratch/jjyeung/envs/sam3_capretry_native_v1/bin:$PATH"
# fla-core 0.6.0 (sha256 b0708b70..., the wheel T0's AWS trainer used) gives the GDN chunk kernels on GPU; CPU runs set MDG_FLA=0.
MDG_FLA_SITE=/scratch/jjyeung/orch_cd/mdg_build/work/fla/site
export PYTHONPATH="$([[ ${MDG_FLA:-1} == 1 ]] && echo "$MDG_FLA_SITE:")/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages:/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME=/scratch/jjyeung/.cache HF_HOME=/scratch/jjyeung/hf
export TRITON_CACHE_DIR=/scratch/jjyeung/.triton
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4

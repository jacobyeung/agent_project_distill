# GX CPU fixture environment (as fx_env.sh, with trainer f5cad828 and its runtime record b7e56bf5).
export FX=/tmp/jjyeung/r1prestage_gxfx
export ANYHOST_JOBS=/scratch/jjyeung/prestage_gx_20261028/closure_src
export R1_MOUNT=$FX R1_TRAINER=/scratch/jjyeung/prestage_gx_20261028/trainer_f5cad828 TRAINER=/scratch/jjyeung/prestage_gx_20261028/trainer_f5cad828
export ANYHOST_NEUTRAL_RUNTIME=/scratch/jjyeung/prestage_gx_20261028/RUNTIME_f5cad828bd12.json
export PATH="$ANYHOST_JOBS/provenance_bin:/scratch/jjyeung/startup_prestage_20261028/venv/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONPATH="$ANYHOST_JOBS/site_alias"
export STUDENT_ORCHARD=1 STUDENT_SLURM_SITE=code-aws CUDA_VISIBLE_DEVICES=
export STUDENT_MODEL_ROOT="$FX/runs/aws128p_20261025/models"
export STUDENT_FRAME_ROOT_MAP="{\"/data2\": \"$FX/data2root\"}"
export HF_HOME="$FX/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false STUDENT_IO_THREADS=4
export R1_STUDENT_HEX=
unset R1_PRESTAGE_DIR R1_PRESTAGE_RECEIPT_SHA256 R1_PRESTAGE_LOCAL R1_PROBE_REGISTRY

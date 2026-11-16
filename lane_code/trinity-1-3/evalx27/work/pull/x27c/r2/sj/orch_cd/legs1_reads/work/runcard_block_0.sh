L=/scratch/jjyeung/orch_cd/legs1_reads
PY=/scratch/jjyeung/envs/p1cpu/bin/python
KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt
F17KIT=/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_eval_gaps
export OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# Set these to the assigned host's actual local inputs, never shared NFS.
: "${RUNROOT:?}" "${FRAMES:?}" "${BASE:?}" "${MODELS:?}"
: "${TOKENIZER:?}" "${TOKENIZER_MANIFEST:?}" "${CARD_PY:?}" "${CARD:?}"
export HF_HOME="$RUNROOT/hf" XDG_CACHE_HOME="$RUNROOT/cache"

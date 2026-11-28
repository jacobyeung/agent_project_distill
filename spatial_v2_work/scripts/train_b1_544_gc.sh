#!/bin/bash
#SBATCH --account=mt01
#SBATCH --partition=advanced
#SBATCH --qos=adv_4gpu_qos
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=64
#SBATCH --mem=480G
#SBATCH --time=1-00:00:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/45e92888780e/logs/j_%j.out
# B1 bound to the step-544 export (artifact 1d6eeb28f51688c4...; archive okh7/i_bb09a77d/m.tar, sha256 3ed73aea...),
# heads dropped, with VLM train-mode + gradient checkpointing enabled in a job-local kit snapshot under /tmp so HF
# GradientCheckpointingLayer (if self.gradient_checkpointing and self.training) activates on Qwen3.5 decoder layers
# while keeping the frozen visual tower in eval mode and the sealed kit untouched.
set -euo pipefail
[ "${1:-}" = B1 ] || { echo "REFUSED: this wrapper binds arm B1 only"; exit 4; }
M544_TAR=${M544_TAR:-/project/community/jjyeung/okh7/i_bb09a77d/m.tar}
PRE=${M544_PRE:-ap/8865619b/runs/469ddece/m544}; ART=${M544_ART:-ap/93ccadab/m544/artifact.json}
WANT_ART=${M544_ART_SHA:-1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef}
X=${TMPDIR_B1:-/tmp}/b15_m544_${SLURM_JOB_ID:-local}; mkdir -p $X
tar xf $M544_TAR -C $X "$PRE/full_weights" "$ART"
got=$(sha256sum $X/$ART | cut -d' ' -f1); [ "$got" = "$WANT_ART" ] || { echo "REFUSED: artifact sha $got != $WANT_ART"; exit 4; }
[ ! -e $X/$PRE/heads.pt ] || { echo "REFUSED: heads.pt extracted"; exit 4; }
cp $X/$ART $X/$PRE/full_weights/student_artifact.json
echo "B1_BIND m544 artifact=$got files=$(ls $X/$PRE/full_weights | tr '\n' ' ')"
export B1_SRC=dir:$X/$PRE/full_weights
cp -r /project/community/jjyeung/45e92888780e/kit $X/kit
python3 - $X/kit/vl_train.py <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = """    if cfg.trainer.get("gradient_checkpointing", False):
        # StarVLA's Qwen3.5 wrapper ignores trainer.gradient_checkpointing; the kit applies it to the VLM here.
        model.qwen_vl_interface.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.qwen_vl_interface.model.config.use_cache = False
        T.logger.info("gradient checkpointing enabled on the VLM")"""
new = """    if cfg.trainer.get("gradient_checkpointing", False):
        # StarVLA's Qwen3.5 wrapper ignores trainer.gradient_checkpointing; from_pretrained() returns eval() mode,
        # which disables HF GradientCheckpointingLayer unless train() is set on the language model.
        model.qwen_vl_interface.model.train()
        model.qwen_vl_interface.model.model.visual.eval()
        model.qwen_vl_interface.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.qwen_vl_interface.model.config.use_cache = False
        model.qwen_vl_interface.model.model.language_model.config.use_cache = False
        T.logger.info("gradient checkpointing enabled on the VLM (train mode active, visual eval, use_cache=False)")"""
assert old in s, "target block not found in vl_train.py"
open(p, "w").write(s.replace(old, new, 1))
PY
export K=$X/kit
export VLL_EXTRA="trainer.gradient_checkpointing=true ${VLL_EXTRA:-}"
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
exec bash ${KIT_TRAIN_ARM:-/project/community/jjyeung/45e92888780e/kit/train_arm.sh} "$@"

R=/project/community/jjyeung/45e92888780e; grep -q ALL_DONE $R/out/rerun_20261116b/phase.log || { echo NOT_DONE; tail -2 $R/out/rerun_20261116b/phase.log; exit 0; }
mkdir -p $R/bind && cat > $R/bind/train_b1_544.sh <<'WRP'
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
# heads dropped: only m544/full_weights (LM + ViT, 760 tensors, header-checked equal in names and shapes to base
# Qwen3.5-9B c2022362) enter the backbone; heads.pt is never extracted. The sealed kit is unchanged: this wrapper
# extracts the members into job-local /tmp and hands stage.sh B1_SRC=dir:..., because the archive keeps artifact.json
# under another prefix (ap/93ccadab/m544/) than full_weights (ap/8865619b/runs/469ddece/m544/), which tarparts: cannot read.
# usage (inside the job, same args as kit/train_arm.sh): sbatch ... train_b1_544.sh B1 [SUBSET] [STEPS] [SEED]
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
exec bash ${KIT_TRAIN_ARM:-/project/community/jjyeung/45e92888780e/kit/train_arm.sh} "$@"
WRP
chmod +x $R/bind/train_b1_544.sh; sha256sum $R/bind/train_b1_544.sh >&2
cd $R/out/rerun_20261116b && tar czf - --exclude="*.mp4" --exclude="*.png" --exclude="*.npz" phase.log sha_check.txt driver.out *.run.log rerun_driver.sh V/out V/logs 2>/dev/null | head -c 15000000

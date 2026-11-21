set -u
cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w30f1 || exit 1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
PY="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
echo "== build $(date -u +%TZ)"; timeout 400 $PY ship/build.py > build.log 2>&1; echo "build rc=$?"; tail -c 7000 build.log
echo "== tchk $(date -u +%TZ)"; timeout 300 $PY ship/tchk.py > tchk.log 2>&1; echo "tchk rc=$?"; tail -c 4000 tchk.log
date -u +%TZ

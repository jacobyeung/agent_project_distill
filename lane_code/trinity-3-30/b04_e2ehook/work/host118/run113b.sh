set -u
B=/dev/shm/jjyeung/b04/host; L=$B/b04_e2ehook; T=$B/tree_rebuild/work/base/tree_b01ce449
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=/dev/shm/jjyeung/b04/pyoverlay; O=$L/parity_kit/host_restore; R=$L/parity_kit/host_results
sha256sum $L/e2e_reader/parity.py
cat > $L/work/host_run_b.sh <<SH
set -u
cd $L
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp OMP_NUM_THREADS=32 CUDA_VISIBLE_DEVICES=
mv $L/parity_kit/E2E_MANIFEST.json $L/parity_kit/E2E_MANIFEST.v1.json; mv $L/parity_kit/E2E_MANIFEST.binding.json $L/parity_kit/E2E_MANIFEST.binding.v1.json
nice -n 10 $PY -B -m parity_kit.build_manifest --root /dev/shm/jjyeung --export-dir $O --g3t /dev/shm/jjyeung/b04/k1/g3t --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST.json > $L/work/manifest_b.log 2>&1
nice -n 10 $PY -B -m parity_kit.cpu_first_batch --settings $L/parity_kit/settings.json --arm own_depth --device cpu --out $R/cpu_first_b > $L/work/first_b.log 2>&1; echo FIRST_DONE >> $L/work/first_b.log
SH
tmux new-session -d -s b04_first "bash $L/work/host_run_b.sh"; sleep 1; tmux ls | grep b04

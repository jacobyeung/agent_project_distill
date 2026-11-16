set -u
B=/dev/shm/jjyeung/b04/host; L=$B/b04_e2ehook; T=$B/tree_rebuild/work/base/tree_b01ce449; M=$L/work/meta/x
PY=/scratch/jjyeung/envs/vllm/bin/python
OV=/dev/shm/jjyeung/b04/pyoverlay
S=/dev/shm/jjyeung/exports/m544; H=/dev/shm/jjyeung/exports/m544_heads
O=$L/parity_kit/host_restore; R=$L/parity_kit/host_results
mkdir -p $L/work/tmp $R
PYTHONPATH=$OV $PY -c "import torchvision, scipy, transformers, torch; print('env ok', torch.__version__, torchvision.__version__, scipy.__version__, transformers.__version__)"
cat > $L/parity_kit/settings.json <<JSON
{"export_dir": "$O", "artifact_manifest": "$L/parity_kit/E2E_MANIFEST.binding.json", "config": "$M/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json", "tree": "$T", "frames_root": "/dev/shm/jjyeung/b04/devs1_frames", "selector_head": "$L/heads/selector/work/run_iso", "scale_head": "$L/heads/scale/work/run1", "sam3": null}
JSON
cat > $L/work/host_run.sh <<SH
set -u
cd $L
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp OMP_NUM_THREADS=32 CUDA_VISIBLE_DEVICES=
nice -n 10 $PY -B -m parity_kit.stage_restore --source $S --heads $H --meta $M --tree $T --out $O > $L/work/restore.log 2>&1; echo RESTORE_RC=\\\$? >> $L/work/restore.log
nice -n 10 $PY -B -m parity_kit.build_manifest --root /dev/shm/jjyeung --export-dir $O --g3t /dev/shm/jjyeung/b04/k1/g3t --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST.json > $L/work/manifest.log 2>&1; echo MANIFEST_RC=\\\$? >> $L/work/manifest.log
nice -n 10 $PY -B -m parity_kit.cpu_first_batch --settings $L/parity_kit/settings.json --arm own_depth --device cpu --out $R/cpu_first > $L/work/first.log 2>&1; echo FIRST_RC=\\\$? >> $L/work/first.log
SH
tmux new-session -d -s b04_first "bash $L/work/host_run.sh"
sleep 2; tmux ls | grep b04; df -h /dev/shm | tail -1; free -g | head -2

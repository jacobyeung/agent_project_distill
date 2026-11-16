set -u
B=/scratch/jjyeung/orch_n30/b04host
L=$B/b04_e2ehook
T=$B/tree_rebuild/work/base/tree_b01ce449
M=$L/work/meta/x
PY=/scratch/jjyeung/envs/p1cpu/bin/python
S=/scratch/jjyeung/orch_n30/b11_presence/work/model_m544
H=/scratch/jjyeung/orch_n30/b04_e2ehook_m544h/m544
G3T=/scratch/jjyeung/k1/g3t
O=$L/parity_kit/host_restore
R=$L/parity_kit/host_results
mkdir -p $L/work/tmp $R
cat > $L/parity_kit/settings.json <<JSON
{"export_dir": "$O", "artifact_manifest": "$L/parity_kit/E2E_MANIFEST.binding.json", "config": "$M/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json", "tree": "$T", "frames_root": "/scratch/jjyeung/devs1_frames", "selector_head": "$L/heads/selector/work/run_iso", "scale_head": "$L/heads/scale/work/run1", "sam3": null}
JSON
cat > $L/work/host_run.sh <<SH
set -u
cd $L
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp OMP_NUM_THREADS=32
nice -n 10 $PY -B -m parity_kit.stage_restore --source $S --heads $H --meta $M --tree $T --out $O > $L/work/restore.log 2>&1; echo RESTORE_RC=\$? >> $L/work/restore.log
nice -n 10 $PY -B -m parity_kit.build_manifest --root /scratch/jjyeung --export-dir $O --g3t $G3T --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST.json > $L/work/manifest.log 2>&1; echo MANIFEST_RC=\$? >> $L/work/manifest.log
nice -n 10 $PY -B -m parity_kit.cpu_first_batch --settings $L/parity_kit/settings.json --arm own_depth --device cpu --out $R/cpu_first > $L/work/first.log 2>&1; echo FIRST_RC=\$? >> $L/work/first.log
SH
tmux new-session -d -s b04_host "bash $L/work/host_run.sh"
sleep 5; tmux has-session -t b04_host && echo STARTED; uptime; nproc

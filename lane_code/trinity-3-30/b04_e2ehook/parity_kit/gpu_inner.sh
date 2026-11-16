#!/bin/bash
set -u
CARD=$1; ARM=$2; NAME=$3; KEYS=$4
V=/scratch/jjyeung/b04shm; B=$V/b04/host2; L=$B/b04_e2ehook; T=$B/tree_rebuild/work/base/tree_b01ce449; M=$L/work/meta/x
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=$V/b04/pyoverlay
O=$L/parity_kit/restore_bw; R=$L/parity_kit/gpu_results
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp
mkdir -p $L/work/tmp $R
cd $L
exec 9>$L/work/prep.lock
flock 9
if [ ! -f $O/RESTORE.json ]; then
  $PY -B -m parity_kit.stage_restore --source $V/exports/m544 --heads $V/exports/m544_heads --meta $M --tree $T --out $O || exit 3
fi
if [ ! -f $L/parity_kit/settings_bw.json ]; then
  printf '{"source_root": "%s", "checkpoint_path": "%s", "receipt_path": "%s"}\n' $V/b05/stage/sam3src $V/b05/stage/sam3.pt \
    $V/b05/lane/code/owngrd/vendor/SAM3_RECEIPT.json > $L/parity_kit/sam3_bw.json
  $PY -B -m parity_kit.build_manifest --root $V --export-dir $O --g3t $V/b04/k1/g3t \
    --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --sam3 $L/parity_kit/sam3_bw.json \
    --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST_bw.json || exit 4
  $PY - <<PYEOF || exit 5
import json
s = dict(export_dir='$O', artifact_manifest='$L/parity_kit/E2E_MANIFEST_bw.binding.json',
         config='$M/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json',
         tree='$T', frames_root='$V/b04/devs1_frames', selector_head='$L/heads/selector/work/run_iso',
         scale_head='$L/heads/scale/work/run1', sam3=json.load(open('$L/parity_kit/sam3_bw.json')), env_roots=['$OV'])
json.dump(s, open('$L/parity_kit/settings_bw.json', 'w'), indent=1)
PYEOF
fi
flock -u 9
if [ "$CARD" = none ]; then echo PREP_ONLY_DONE; exit 0; fi
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
CUDA_VISIBLE_DEVICES=$CARD /data3/shared/scripts/vnice/vnice.sh $PY -B -m parity_kit.run_parity \
  --settings $L/parity_kit/settings_bw.json --arm $ARM --device cuda:0 --out $R/$NAME ${KEYS:+--keys $KEYS}

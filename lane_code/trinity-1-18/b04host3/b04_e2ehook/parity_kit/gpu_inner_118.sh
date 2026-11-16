#!/bin/bash
# GPU parity read on trinity-1-18 (no bwrap: every input is on local /scratch). Usage: gpu_inner_118.sh CARD|none|cpu ARM NAME [KEYS]
set -u
CARD=$1; ARM=$2; NAME=$3; KEYS=${4:-}
H=/scratch/jjyeung/orch_n30/b04host3; L=$H/b04_e2ehook; T=$H/tree_rebuild/work/base/tree_b01ce449; M=$L/work/meta/x
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=$H/pyoverlay
O=$L/parity_kit/restore_118; R=$L/parity_kit/gpu_results
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp
mkdir -p $L/work/tmp $R
cd $L
exec 9>$L/work/prep.lock
flock 9
if [ ! -f $O/RESTORE.json ]; then
  $PY -B -m parity_kit.stage_restore --source /scratch/jjyeung/orch_n30/b11_presence/work/model_m544 \
    --heads /scratch/jjyeung/orch_n30/b04_e2ehook_m544h/m544 --meta $M --tree $T --out $O || exit 3
fi
if [ ! -f $L/parity_kit/settings_118.json ]; then
  printf '{"source_root": "%s", "checkpoint_path": "%s", "receipt_path": "%s"}\n' /scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src \
    /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt /scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd/vendor/SAM3_RECEIPT.json > $L/parity_kit/sam3_118.json
  $PY -B -m parity_kit.build_manifest --root /scratch/jjyeung --export-dir $O --g3t /scratch/jjyeung/k1/g3t \
    --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --sam3 $L/parity_kit/sam3_118.json \
    --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST_118.json || exit 4
  $PY - <<PYEOF || exit 5
import json
s = dict(export_dir='$O', artifact_manifest='$L/parity_kit/E2E_MANIFEST_118.binding.json',
         config='$M/fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json',
         tree='$T', frames_root='/scratch/jjyeung/devs1_frames', selector_head='$L/heads/selector/work/run_iso',
         scale_head='$L/heads/scale/work/run1', sam3=json.load(open('$L/parity_kit/sam3_118.json')), env_roots=['$OV'])
json.dump(s, open('$L/parity_kit/settings_118.json', 'w'), indent=1)
s['sam3'] = None
json.dump(s, open('$L/parity_kit/settings_118_nosam.json', 'w'), indent=1)
PYEOF
fi
flock -u 9
if [ "$CARD" = none ]; then echo PREP_ONLY_DONE; exit 0; fi
if [ "$CARD" = cpu ]; then
  OMP_NUM_THREADS=24 nice -n 10 $PY -B -m parity_kit.run_parity --settings $L/parity_kit/settings_118_nosam.json --arm $ARM --device cpu --out $R/$NAME ${KEYS:+--keys $KEYS}
  exit $?
fi
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
CUDA_VISIBLE_DEVICES=$CARD /data3/shared/scripts/vnice/vnice.sh $PY -B -m parity_kit.run_parity \
  --settings $L/parity_kit/settings_118.json --arm $ARM --device cuda:0 --out $R/$NAME ${KEYS:+--keys $KEYS}

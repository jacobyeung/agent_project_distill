#!/bin/bash
# Rebuild the 1-18 artifact manifest for the current reader (grounding d9b7e6f3) under new names; old 118 files stay.
set -u
H=/scratch/jjyeung/orch_n30/b04host3; L=$H/b04_e2ehook; T=$H/tree_rebuild/work/base/tree_b01ce449; M=$L/work/meta/x
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=$H/pyoverlay; O=$L/parity_kit/restore_118
export PYTHONPATH=$OV PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp
cd $L
test ! -e $L/parity_kit/E2E_MANIFEST_118b.json || { echo EXISTS; exit 2; }
$PY -B -m parity_kit.build_manifest --root /scratch/jjyeung --export-dir $O --g3t /scratch/jjyeung/k1/g3t \
  --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --sam3 $L/parity_kit/sam3_118.json \
  --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST_118b.json || exit 4
$PY - <<PYEOF || exit 5
import json
s = json.load(open('$L/parity_kit/settings_118.json'))
s['artifact_manifest'] = '$L/parity_kit/E2E_MANIFEST_118b.binding.json'
json.dump(s, open('$L/parity_kit/settings_118b.json', 'w'), indent=1)
s['sam3'] = None
json.dump(s, open('$L/parity_kit/settings_118b_nosam.json', 'w'), indent=1)
PYEOF
ls -la $L/parity_kit/E2E_MANIFEST_118b* $L/parity_kit/settings_118b*
OMP_NUM_THREADS=24 nice -n 10 $PY -B -m parity_kit.run_parity --settings $L/parity_kit/settings_118b_nosam.json --arm own_depth --device cpu --out $L/parity_kit/gpu_results/cpu_cam1_118b --keys $L/work/key_cam1.txt 2>&1 | grep -v -i "warn\|fast path" | tail -20
echo "CPU_RC=${PIPESTATUS[0]}"

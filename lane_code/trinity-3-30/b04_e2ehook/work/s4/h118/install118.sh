L=/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook
cat > $L/parity_kit/gpu_inner_118.sh <<'XEOF'
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
XEOF
cat > $L/parity_kit/launch_118.sh <<'XEOF'
#!/bin/bash
# usage: launch_118.sh CARD ARM NAME KEYS_FILE   (only on a card the orchestrator named; two empty readings 330 s apart; HOLD file and new main inbox naming 1-18 stop it)
CARD=$1; ARM=$2; NAME=$3; KEYS=$4
L=/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook; LOG=$L/work/gpu_launch.log; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
rd() { echo "$(nvidia-smi -i $CARD --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' ') $(nvidia-smi -i $CARD --query-compute-apps=pid --format=csv,noheader | wc -l)"; }
held() { [ -e $L/work/HOLD ] && return 0; n=$(ls -t $O/INBOX_TO_DISTILL_ORCH_* | head -1); [ "$(basename $n)" != INBOX_TO_DISTILL_ORCH_20261116T172517Z.md ] && grep -q "1-18" $n && return 0; return 1; }
if held; then echo "$(date -u +%FT%TZ) HOLD before $NAME" >> $LOG; exit 0; fi
set -- $(rd); echo "$(date -u +%FT%TZ) card$CARD reading1 mem=$1 procs=$2 before $NAME" >> $LOG; [ "$1" -le 10 ] && [ "$2" -eq 0 ] || { echo "$(date -u +%FT%TZ) NOT_EMPTY" >> $LOG; exit 0; }
sleep 330
if held; then echo "$(date -u +%FT%TZ) HOLD before $NAME" >> $LOG; exit 0; fi
set -- $(rd); echo "$(date -u +%FT%TZ) card$CARD reading2 mem=$1 procs=$2 before $NAME" >> $LOG; [ "$1" -le 10 ] && [ "$2" -eq 0 ] || { echo "$(date -u +%FT%TZ) NOT_EMPTY" >> $LOG; exit 0; }
echo "$(date -u +%FT%TZ) LAUNCH $NAME card $CARD" >> $LOG
bash $L/parity_kit/gpu_inner_118.sh $CARD $ARM $NAME $KEYS > $L/work/gpu_$NAME.log 2>&1
echo "$(date -u +%FT%TZ) ${NAME}_EXIT $?" >> $LOG
XEOF
cat > $L/parity_kit/prep118.sh <<'XEOF'
#!/bin/bash
# one-time prep on trinity-1-18: overlay env, restore + manifest, SAM 3 probe, one CPU camera item (SAM 3 off)
H=/scratch/jjyeung/orch_n30/b04host3; L=$H/b04_e2ehook; LOG=$L/work/prep118.log; mkdir -p $L/work
{
echo "$(date -u +%FT%TZ) PREP start"
OV=$H/pyoverlay; mkdir -p $OV
P=$(ls -d /scratch/jjyeung/envs/p1cpu/lib/python3*/site-packages); S=/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages
cp -a $P/scipy $P/scipy.libs $P/scipy-1.14.1.dist-info $OV/ 2>&1
for p in iopath portalocker ftfy timm pycocotools wcwidth; do cp -a $S/$p $S/$p-*.dist-info $OV/ 2>&1; done
ls $OV | tr '\n' ' '; echo
bash $L/parity_kit/gpu_inner_118.sh none own_depth prep; echo "PREP_RC=$?"
cd $L && PYTHONPATH=$OV /scratch/jjyeung/envs/vllm/bin/python -B -m parity_kit.sam3_probe --source-root /scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src --checkpoint /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt --tree $H/tree_rebuild/work/base/tree_b01ce449 2>&1 | tail -20; echo "PROBE_RC=$?"
head -1 $L/parity_kit/keys_smoke.txt > $L/work/key_cam1.txt
bash $L/parity_kit/gpu_inner_118.sh cpu own_depth cpu_cam1_118 $L/work/key_cam1.txt 2>&1 | grep -v -i "warn\|fast path" | tail -20; echo "CPU_RC=$?"
echo "$(date -u +%FT%TZ) PREP end"
} >> $LOG 2>&1
XEOF
cd $L && sha256sum parity_kit/*_118.sh parity_kit/prep118.sh && tmux new-session -d -s b04_prep118 "bash parity_kit/prep118.sh" && tmux ls | grep b04_

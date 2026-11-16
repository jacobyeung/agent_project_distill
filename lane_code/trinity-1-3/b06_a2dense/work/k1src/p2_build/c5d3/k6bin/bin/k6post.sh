#!/bin/bash
# merge -> install test into node-local /tmp -> validation (with release ARKit mp4s for the orientation check)
set -u
F=/project/community/jjyeung/cp4tk_fr
PY=$F/venv/bin/python
J=${SLURM_JOB_ID:-x}_${SLURM_RESTART_COUNT:-0}
L=/tmp/jjy_tk_fv_$J; mkdir -p $L/root $L/mp4
echo "start post $(hostname) $(date -u +%FT%TZ) job $J"
# ARKit release archive for the 10-capture orientation check (node-local only), in the background
B=https://huggingface.co/datasets/nyu-visionx/VSI-590K/resolve/346fbd4e
( python3 $F/bin/rdl.py $B/arkitscenes.tar.gz $L/arkitscenes.tar.gz 90154741781 4c54a042dd9c3ca808a61d05536598878d93a1b395b668551daec19895da9728 32 64 > $L/dl.log 2>&1
  $PY -c "import json;[print('*/'+c['vid']+'.mp4') for c in json.load(open('$F/bin/val_cfg.json'))['ncc']]" > $L/mp4_members.txt
  tar -I pigz -xf $L/arkitscenes.tar.gz -C $L/mp4 --wildcards -T $L/mp4_members.txt; echo "mp4 extract rc=$?" >> $L/dl.log ) &
DLP=$!
$PY $F/bin/k6merge.py $F $F/k6tk || { echo "merge failed"; exit 1; }
echo "merge done $(date -u +%FT%TZ)"
$PY $F/bin/k6install.py --root $L/root --src $F/k6tk/parts --meta $F/k6tk --sample 5000 --verify-shards > $F/k6tk/install_test.log 2>&1; echo "install rc=$? $(tail -1 $F/k6tk/install_test.log)"
wait $DLP; cat $L/dl.log | tail -3; find $L/mp4 -name '*.mp4' | head -20
$PY $F/bin/k6val.py $F $L/root $L/mp4 $F/k6tk/VALIDATION.json || echo "val failed"
echo "end post $(date -u +%FT%TZ)"

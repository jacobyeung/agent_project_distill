#!/usr/bin/env bash
# Inside sbx.sh fcopy: the gate.py:55 edit refuses non-regular plants and keeps the legitimate flow.
set -u
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
L=/scratch/jjyeung/orch_n30/sb_ph2chk/work/logs/patch_check.txt
KIT=/scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase
PY=/scratch/jjyeung/envs/p1cpu/bin/python
cd "$KIT"
: > $L
bash run.sh part2/test_part2.py > ${L%.txt}_part2.log 2>&1; echo "part2 rc=$? $(tail -n 1 ${L%.txt}_part2.log)" >> $L
bash run.sh part2/test_launcher.py > ${L%.txt}_launcher.log 2>&1; echo "launcher rc=$? $(tail -n 1 ${L%.txt}_launcher.log)" >> $L
# Legitimate: logs dir and capture log in out/part2 must still admit the aggregate.
mkdir -p out/part2/logs && echo log > out/part2/logs/capture.log
$PY -B part2/gate.py aggregate >> $L 2>&1; echo "legit logs: gate aggregate rc=$?" >> $L
mkdir work/pc_clean && cp -a work/part2_fixture/caps work/pc_clean/
PART2_FIXTURE_DIR=work/pc_clean bash run.sh part2/price.py fixture-aggregate > ${L%.txt}_clean_agg.log 2>&1
echo "clean fixture-aggregate rc=$? $(tail -n 1 ${L%.txt}_clean_agg.log | cut -c1-160)" >> $L
for kind in dir fifo; do
  d=work/pc_$kind; mkdir -p $d/aggregate && cp -a work/part2_fixture/caps $d/
  if [[ $kind == dir ]]; then mkdir $d/aggregate/DECISION_PART2.json; else mkfifo $d/aggregate/DECISION_PART2.json; fi
  PART2_FIXTURE_DIR=$d bash run.sh part2/price.py fixture-aggregate > ${L%.txt}_$kind.log 2>&1
  echo "reach $kind rc=$? files=$(ls $d/aggregate | tr '\n' ' ') msg=$(tail -n 1 ${L%.txt}_$kind.log | cut -c1-160)" >> $L
done
mkdir out/part2/PER_ITEM_PART2.jsonl
$PY -B part2/gate.py aggregate >> $L 2>&1; echo "dir PER_ITEM: gate aggregate rc=$?" >> $L
rmdir out/part2/PER_ITEM_PART2.jsonl
mkdir -p work/part2_caps/arkitscenes__41048124.json.gz
$PY -B part2/gate.py capture >> $L 2>&1; echo "dir caps gz: gate capture rc=$?" >> $L
echo DONE >> $L

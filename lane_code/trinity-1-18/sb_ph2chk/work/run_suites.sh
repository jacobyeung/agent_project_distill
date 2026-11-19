#!/usr/bin/env bash
# Inside sbx.sh scopy: suites, dry-run, fresh fixture, fresh fixture-aggregate, CPU STEP5.
set -u
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
LOGS=/scratch/jjyeung/orch_n30/sb_ph2chk/work/logs
KIT=/scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase
cd /scratch/jjyeung/orch_n30/sb_ph2fix
S=$LOGS/suites_summary.txt
echo "kit realpath: $(realpath sb_mask_phrase/part2/gate.py)" > $S
step() {
  local name=$1; shift
  local start=$(date +%s)
  "$@" > $LOGS/suite_$name.log 2>&1
  local rc=$?
  echo "$name rc=$rc seconds=$(( $(date +%s) - start )) tail=$(tail -n 3 $LOGS/suite_$name.log | tr '\n' ' ' | cut -c1-220)" >> $S
}
step part1 bash sb_mask_phrase/run.sh test_kit.py
step part2 bash sb_mask_phrase/run.sh part2/test_part2.py
step launcher bash sb_mask_phrase/run.sh part2/test_launcher.py
step dryrun bash sb_mask_phrase/run.sh dryrun.py report
step fixture env PART2_FIXTURE_DIR=work/chk_fixture bash sb_mask_phrase/run.sh part2/price.py fixture arkitscenes/41048124,scannetpp/067e2e4e61
mkdir "$KIT/work/chk_aggregate" && cp -a "$KIT/work/part2_fixture/caps" "$KIT/work/chk_aggregate/"
step aggregate env PART2_FIXTURE_DIR=work/chk_aggregate bash sb_mask_phrase/run.sh part2/price.py fixture-aggregate
step step5_cpu env PART2_GO=1 bash sb_mask_phrase/run.sh part2/sam3_pass.py step5
echo DONE >> $S

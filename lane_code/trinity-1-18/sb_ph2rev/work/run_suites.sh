#!/usr/bin/env bash
# Rerun part 1, part 2, launcher suites and dry-run steps 1-4 on the extracted tar, bound at the kit's own path.
# Runs inside: bwrap --dev-bind / / --dev /dev --bind work/extract /scratch/jjyeung/orch_n30/sb_ph2fix
set -u
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
LOGS=/scratch/jjyeung/orch_n30/sb_ph2rev/work/logs
cd /scratch/jjyeung/orch_n30/sb_ph2fix
echo "kit realpath: $(realpath sb_mask_phrase/part2/gate.py)" > $LOGS/suites_summary.txt
for spec in "part1:test_kit.py" "part2:part2/test_part2.py" "launcher:part2/test_launcher.py" "dryrun:dryrun.py report"; do
  name=${spec%%:*}; args=${spec#*:}
  start=$(date +%s)
  bash sb_mask_phrase/run.sh $args > $LOGS/suite_$name.log 2>&1
  rc=$?
  echo "$name rc=$rc seconds=$(( $(date +%s) - start )) tail=$(tail -n 3 $LOGS/suite_$name.log | tr '\n' ' ' | cut -c1-200)" >> $LOGS/suites_summary.txt
done
echo DONE >> $LOGS/suites_summary.txt

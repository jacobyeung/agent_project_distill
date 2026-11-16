#!/bin/bash
# Runs each test directory of the clone with /home and /data* hidden; 90 s cap per directory.
C=/scratch/jjyeung/orch_n30/eff_audit/repo/clone
O=/scratch/jjyeung/orch_n30/eff_audit/repo/tests
PY=/scratch/jjyeung/envs/p1cpu/bin/python
for d in collector gt_adapters/arkit gt_adapters/scannet_v1 gt_adapters/scannet_v2 gt_adapters/scannetpp_multilabel materialize/wrapper_codex_v1 materialize/wrapper_prep_v2 materialize/wrapper_scannet_v1 orchard/stages/qwen36_27b_answeronly preparers/scannet_v3 student/compact_targets student/eval-harness student/landing student/shakedown tools/gtmeasure tools/paper_tables tools/tests tools/test_provenance.py; do
  n=$(echo $d | tr '/' '_')
  ( cd $C/$(dirname $d) 2>/dev/null; cd $C/$d 2>/dev/null || cd $C/$(dirname $d)
    timeout 90 bwrap --ro-bind / / --bind /scratch/jjyeung/orch_n30/eff_audit/repo /scratch/jjyeung/orch_n30/eff_audit/repo --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc --chdir "$PWD" \
      env HOME=/tmp PYTHONDONTWRITEBYTECODE=1 $PY -s -m pytest -q -p no:cacheprovider --tb=line -o addopts="" $C/$d > $O/$n.txt 2>&1
    echo "rc=$?" >> $O/$n.txt )
  echo "$d: $(tail -2 $O/$n.txt | tr '\n' ' ')"
done

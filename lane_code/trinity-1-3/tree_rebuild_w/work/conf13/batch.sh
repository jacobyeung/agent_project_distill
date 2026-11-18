#!/bin/bash
cd /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/pkg
for s in test13.py census13.py mapping13.py edges13.py mutations13.py; do echo "== $s $(date -u +%T)"; timeout 3000 bash /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/run.sh work/build13/$s > /scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/${s%.py}.log 2>&1; echo "rc=$?"; done
echo DONE $(date -u +%T)

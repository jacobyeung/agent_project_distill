W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1e; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ
cat /scratch/jjyeung/orch_n30/tr19_revC1/work/run_tests.py
for f in BUILD24M4L_REPORT.md TREE_CPRIME.md QD_STEP1.md; do echo "@@@ $f"; cat $W/w24l/out/$f; done
ls -la $W/w24m $W/w24m/out 2>&1 | tail -30

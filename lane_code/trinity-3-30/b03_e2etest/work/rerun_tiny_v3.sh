#!/bin/bash
# EAT-1 v3 (post-review kit) reruns of the four tiny baselines
L=/scratch/jjyeung/orch_n30/b03_e2etest; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $L
C8=$L/work/audit_copies/tree_b01ce449; B5=$L/work/nextleg/b5/work/tree_r1
run() { W=$1; R=$2; T=$3; N=$4; shift 4
  timeout 2400 $P -B -m eat1.run --reader eat1.adapters.$R:make_reader --reader-kwargs "$T" --items $W/items.jsonl --out $W/$N --perturb --sandbox "$@" > $W/$N.log 2>&1; echo "$W/$N rc=$? $(tail -1 $W/$N.log)"; }
run work/c8r_tiny c8r_tiny "{\"tree\": \"$C8\", \"workdir\": \"$L/work/c8r_tiny\"}" run9 --code-root $C8
run work/b5_tiny c8r_tiny "{\"tree\": \"$B5\", \"workdir\": \"$L/work/b5_tiny\"}" run4 --code-root $B5
run work/b5_gf1_tiny gf1_tiny "{\"tree\": \"$B5\", \"workdir\": \"$L/work/b5_gf1_tiny\"}" run7 --code-root $B5
run work/b04_tiny2 b04_tiny "{\"workdir\": \"$L/work/b04_tiny2\"}" run5 --code-root /scratch/jjyeung/orch_n30/b04_e2ehook --allowlist-extra eat1/adapters/b04_allow.json
echo ALLDONE

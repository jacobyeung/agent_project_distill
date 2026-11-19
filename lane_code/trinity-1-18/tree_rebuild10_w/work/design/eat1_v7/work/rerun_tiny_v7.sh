#!/bin/bash
# EAT-1 v7 (post-round-5 kit); outputs in /tmp/jjyeung_b03/tiny (3-30 /scratch is at its floor) reruns of the four tiny baselines
L=/scratch/jjyeung/orch_n30/b03_e2etest; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $L
C8=$L/work/audit_copies/tree_b01ce449; B5=$L/work/nextleg/b5/work/tree_r1
mkdir -p /tmp/jjyeung_b03/tiny/{c8r_tiny,b5_tiny,b5_gf1_tiny}
export EAT1_TMP=/tmp/jjyeung_b03 TMPDIR=/tmp/jjyeung_b03
run() { W=$1; R=$2; T=$3; N=$4; shift 4
  timeout 2400 $P -B -m eat1.run --reader eat1.adapters.$R:make_reader --reader-kwargs "$T" --items $W/items.jsonl --out /tmp/jjyeung_b03/tiny/$(basename $W)/$N --perturb --sandbox "$@" > /tmp/jjyeung_b03/tiny/$(basename $W)/$N.log 2>&1; echo "$W/$N rc=$? $(tail -1 /tmp/jjyeung_b03/tiny/$(basename $W)/$N.log)"; }
run work/c8r_tiny c8r_tiny "{\"tree\": \"$C8\", \"workdir\": \"$L/work/c8r_tiny\"}" run13 --code-root $C8
run work/b5_tiny c8r_tiny "{\"tree\": \"$B5\", \"workdir\": \"$L/work/b5_tiny\"}" run8 --code-root $B5
run work/b5_gf1_tiny gf1_tiny "{\"tree\": \"$B5\", \"workdir\": \"$L/work/b5_gf1_tiny\"}" run11 --code-root $B5
echo ALLDONE

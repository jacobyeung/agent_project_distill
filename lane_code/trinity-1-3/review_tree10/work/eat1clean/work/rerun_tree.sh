#!/bin/bash
# Usage: bash work/rerun_tree.sh <unpacked tree root> <tag>   (EAT-1 static scan + both tiny adapters on a next-leg tree)
set -eu
L=/scratch/jjyeung/orch_n30/b03_e2etest; T=$(readlink -f "$1"); G=$2; P=/scratch/jjyeung/envs/p1cpu/bin/python
cd $L; O=$L/work/nextleg/$G; mkdir -p $O
sed "s#.*/tree_r1/#$T/#" work/nextleg/static/SCOPE_READ.txt > $O/SCOPE_READ.txt
$P -B -m eat1.scan $(cat $O/SCOPE_READ.txt) --json $O/SCAN_READ.json
for f in $(cat $O/SCOPE_READ.txt); do r=${f#$T/}; cmp -s work/nextleg/b5/work/tree_r1/$r $f || echo "CHANGED_VS_B5 $r"; done > $O/CHANGED_VS_B5.txt
python3 work/findings_md.py $O/SCAN_READ.json $O/FINDINGS_READ.md "EAT-1 static findings: next-leg tree $G read path"
for a in c8r_tiny gf1_tiny; do W=$O/$a; mkdir -p $W; cp work/$([ $a = c8r_tiny ] && echo c8r_tiny || echo b5_gf1_tiny)/items.jsonl $W/
  timeout 1800 $P -B -m eat1.run --reader eat1.adapters.$a:make_reader --reader-kwargs "{\"tree\": \"$T\", \"workdir\": \"$W\"}" \
    --items $W/items.jsonl --out $W/run --code-root $T --perturb --sandbox > $W/run.log 2>&1 || true; tail -1 $W/run.log; done
cat $O/CHANGED_VS_B5.txt

#!/bin/bash
# usage: mk34.sh <label> <kit dir relative to W/w34: test1/n_go or n_go>; stages fix16's current DIFF + cand and fix17/in into s/<label>.sh
set -eu; F17=/scratch/jjyeung/orch_n30/tree_rebuild28/work/fix17; L=/scratch/jjyeung/orch_n30/tree_rebuild28/work; LB=$1; KD=$2
ST=$F17/stage_$LB; mkdir -p $ST/cand/b $ST/cand/k $ST/ut
cp $L/fix16/DIFF.patch $ST/; cp $L/fix16/cand/j.sh $L/fix16/cand/SHA256SUMS.expected.txt $ST/cand/; cp $L/fix16/cand/b/a.py $L/fix16/cand/b/pf.py $ST/cand/b/; cp $L/fix16/cand/k/j.json $ST/cand/k/
cp $F17/in/b34.py $F17/in/st34.py $F17/in/fu34.py $L/fix12/in/tchk33.py $L/fix12/in/t1_33.py $ST/; cp $L/fix12/in/ut/ut2.py $ST/ut/; (cd $L/fix12/in/ut && tar cf - --exclude=__pycache__ fake) | tar xf - -C $ST/ut
DSHA=$(sha256sum $ST/DIFF.patch | cut -c1-64); echo "DIFF $DSHA"
{ echo "set -u; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=\$W/w34; LB=$LB; KD=$KD; DSHA=$DSHA; mkdir -p \$F/in_\$LB \$F/\$LB && cd \$F"
  echo "echo '$(tar czf - -C $ST . | base64 -w0)' | base64 -d | tar xzf - -C in_\$LB"
  cat $F17/s/body34.sh
} > $F17/s/$LB.sh; wc -c $F17/s/$LB.sh

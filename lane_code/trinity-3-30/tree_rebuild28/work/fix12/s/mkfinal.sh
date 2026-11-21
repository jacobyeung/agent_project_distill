#!/bin/bash
# usage: mkfinal.sh <label> <outkit relative to w33n, e.g. n_go> ; packs ./in into the remote script s/<label>.sh
set -eu; cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix12; LB=$1; KD=$2
{ echo "set -u; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=\$W/w33n; LB=$LB; KD=$KD; mkdir -p \$F/in_\$LB \$F/\$LB && cd \$F"
  echo "echo '$(tar czf - -C in . | base64 -w0)' | base64 -d | tar xzf - -C in_\$LB"
  cat <<'EOF'
sha256sum in_$LB/*; df -h /scratch | tail -1
PY="nice -n 10 timeout 500 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
$PY in_$LB/b33.py $F/$KD $F/in_$LB > $LB/build.log 2>&1; echo build_rc=$?; grep -E '"seal"|verify_kit|py_compile_all_ok|j_method' $LB/build.log
[ -f $F/BUILD33.json ] && mv $F/BUILD33.json $LB/ ; [ -f $F/j_merged.sh ] && mv $F/j_merged.sh $LB/
$PY in_$LB/tchk33.py $F/$KD > $LB/tchk.log 2>&1; echo tchk_rc=$?; grep 'receipts(cfg)' $LB/tchk.log
$PY in_$LB/t1_33.py $F/$KD > $LB/t1.log 2>&1; echo t1_rc=$?; [ -f $F/TEST_T1_33.json ] && mv $F/TEST_T1_33.json $LB/; grep -E 'T3|T4|ok"' $LB/TEST_T1_33.json | head
$PY in_$LB/fu33.py $F/$KD > $LB/fu.log 2>&1; echo fu_rc=$?; [ -f $F/TEST_FRAMES_33.json ] && mv $F/TEST_FRAMES_33.json $LB/; grep all_as_expected $LB/TEST_FRAMES_33.json
[ -f in_$LB/ut/ut2.py ] && { $PY in_$LB/ut/ut2.py $F/$KD/b > $LB/extra_ut2.log 2>&1; echo ut2_rc=$?; tail -c 300 $LB/extra_ut2.log; }
for x in in_$LB/extra_*.py; do [ -f "$x" ] || continue; n=$(basename $x .py); $PY $x $F/$KD > $LB/$n.log 2>&1; echo $n rc=$?; tail -c 600 $LB/$n.log; done
cp $F/$KD/SHA256SUMS.txt $LB/SHA256SUMS.txt
if [ "$KD" = n_go ]; then
  tar cf s33n_n_go.tar n_go && sha256sum s33n_n_go.tar > s33n_n_go.tar.sha256 && cat s33n_n_go.tar.sha256; ls -l s33n_n_go.tar
  ssh -o ConnectTimeout=20 trinity-3-30.ib 'mkdir -p /scratch/jjyeung/n30_mirror/tree_rebuild28/fix12' </dev/null
  tar cf - s33n_n_go.tar s33n_n_go.tar.sha256 $LB/BUILD33.json </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/n30_mirror/tree_rebuild28/fix12 && tar xf - && sha256sum s33n_n_go.tar'
fi
tar cf - $LB </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix12/rd && tar xf - && echo GOT_RD'
echo END
EOF
} > s/$LB.sh; wc -c s/$LB.sh

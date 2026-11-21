hostname -s; date -u +%FT%TZ; (cd in_$LB && find . -type f | sort | xargs sha256sum); df -h /scratch | tail -1
PY="nice -n 10 timeout 500 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
$PY in_$LB/b34.py $F/$KD $F/in_$LB $DSHA > $LB/build.log 2>&1; echo build_rc=$?
P=$(dirname $F/$KD); if [ "$P" != "$F/$LB" ]; then for x in BUILD34.json j_old.sh j_new.sh; do [ -f $P/$x ] && mv $P/$x $LB/; done; fi
grep -E '"seal"|verify_kit|zseal|py_compile_all_ok|j_bash_n_rc|capsule_writer|offset_or_fuzz|BUILD_only' $LB/build.log
$PY in_$LB/tchk33.py $F/$KD > $LB/tchk.log 2>&1; echo tchk_rc=$?; grep 'receipts(cfg)' $LB/tchk.log
$PY in_$LB/t1_33.py $F/$KD > $LB/t1.log 2>&1; echo t1_rc=$?; [ -f $P/TEST_T1_33.json ] && mv $P/TEST_T1_33.json $LB/; grep -E 'T3|T4|ok"' $LB/TEST_T1_33.json | head
$PY in_$LB/fu34.py $F/$KD A $F/$LB/TEST_FRAMES_A.json > $LB/fuA.log 2>&1; echo fuA_rc=$?; grep all_as_expected $LB/TEST_FRAMES_A.json
HB=$F/$LB/nsB; OB=$F/$LB/otherB; mkdir -p $HB/p/q/fu/root3 $OB
bwrap --dev-bind / / --tmpfs /tmp --bind $HB /tmp/q_22c714e1 --bind $HB /tmp/jjyeung/q_22c714e1 --bind $OB /tmp/jjyeung/q_22c714e1/p/q/fu/root3 $PY in_$LB/fu34.py $F/$KD B $F/$LB/TEST_FRAMES_B.json > $LB/fuB.log 2>&1; echo fuB_rc=$?; grep all_as_expected $LB/TEST_FRAMES_B.json
$PY in_$LB/ut/ut2.py $F/$KD/b > $LB/ut2.log 2>&1; echo ut2_rc=$?; tail -c 200 $LB/ut2.log; echo
$PY in_$LB/st34.py $F/$KD $W/w33n/n_go > $LB/static.log 2>&1; echo static_rc=$?; grep -E '"check_|all_ok' $LB/static.log
$PY -c "import sys; sys.path.insert(0,'$W/w30f1/tree'); from launch_r1.build import verify; print('launch_r1.build.verify', verify('$F/$KD'))" 2>&1 | tee $LB/verify.log
cp $F/$KD/SHA256SUMS.txt $LB/SHA256SUMS.txt; sha256sum $F/$KD/SHA256SUMS.txt
if [ "$KD" = n_go ]; then
  tar cf s34_n_go.tar n_go && sha256sum s34_n_go.tar > s34_n_go.tar.sha256 && cat s34_n_go.tar.sha256; ls -l s34_n_go.tar
  ssh -o ConnectTimeout=20 trinity-3-30.ib 'mkdir -p /scratch/jjyeung/n30_mirror/tree_rebuild28/fix17' </dev/null
  tar cf - s34_n_go.tar s34_n_go.tar.sha256 $LB/BUILD34.json </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/n30_mirror/tree_rebuild28/fix17 && tar xf - && sha256sum s34_n_go.tar'
fi
tar cf - --exclude=nsB --exclude=otherB --exclude=futmpA --exclude=t1tmp $LB </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix17/rd && tar xf - && echo GOT_RD'
echo END

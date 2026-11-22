hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1; [[ "$(hostname -s)" == trinity ]] && exit 9
I=$F/in_$LB; O=$F/$LB; cd $F
(cd $I && find . -type f | sort | xargs sha256sum) > $O/inputs.sha256
PY="nice -n 10 timeout 900 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
$PY $I/in/tree35.py $W/w34/n_go $O/tree35 timeout > $O/tree35.log 2>&1; echo tree35_rc=$?; grep -E 'new_seal|new_tar_sha256' $O/tree35.log
echo "sealed tree tar on node: $(sha256sum $F/tree2/t_db42866fd9e8d009.tar | cut -c1-64) rebuilt: $(sha256sum $O/tree35/t_db42866fd9e8d009.tar | cut -c1-64)"
$PY $I/in/b35.py $W/w34/n_go $O/n_go $O/tree35 $I/new > $O/build.log 2>&1; echo build_rc=$?; grep -E '"seal"|verify_new_tree|py_compile_all_ok|bash_n_rc|capsule_writer|pycache' $O/build.log
K=$O/n_go
$PY $I/f17/tchk33.py $K > $O/tchk.log 2>&1; echo tchk_rc=$?; grep 'receipts(cfg)' $O/tchk.log
$PY $I/f17/t1_33.py $K > $O/t1.log 2>&1; echo t1_rc=$?; grep -E 'T3|T4|ok"' $O/TEST_T1_33.json | head
$PY $I/f17/fu34.py $K A $O/TEST_FRAMES_A.json > $O/fuA.log 2>&1; echo fuA_rc=$?; grep all_as_expected $O/TEST_FRAMES_A.json
HB=$O/nsB; OB=$O/otherB; mkdir -p $HB/p/q/fu/root3 $OB
bwrap --dev-bind / / --tmpfs /tmp --bind $HB /tmp/q_22c714e1 --bind $HB /tmp/jjyeung/q_22c714e1 --bind $OB /tmp/jjyeung/q_22c714e1/p/q/fu/root3 $PY $I/f17/fu34.py $K B $O/TEST_FRAMES_B.json > $O/fuB.log 2>&1; echo fuB_rc=$?; grep all_as_expected $O/TEST_FRAMES_B.json
$PY $I/f17/ut/ut2.py $K/b > $O/ut2.log 2>&1; echo ut2_rc=$?; tail -c 200 $O/ut2.log; echo
$PY $I/f17/st34.py $K $W/w33n/n_go > $O/static.log 2>&1; echo static_rc=$?; grep -E '"check_|all_ok' $O/static.log
$PY -c "import json,base64,sys;c=json.load(open(sys.argv[1]));open(sys.argv[2],'wb').write(base64.b64decode(c['payload']))" $W/w34/n_go/k/c.json $O/c_base.raw
for t in old new; do $PY $I/in/tmil_test.py $O/tree35/$t $O/c_base.raw $t > $O/tmil_$t.json 2>&1; echo "tmil_$t rc=$? $(grep -c PASS $O/tmil_$t.json) PASS lines"; done
for t in old new; do $PY $I/in/cc_test.py $O/tree35/$t $I/in/pc/p_config.json $I/in/pc/v174246.json > $O/cc_$t.json 2>&1; echo "cc_$t: $(tr -d '\n' < $O/cc_$t.json | grep -o '"results".*')"; done
$PY $I/test/mreaders.py $O/tree35/new $K $I/in/pc/p_config.json $I/test/v_100_200.json > $O/mreaders.json 2>&1; echo mreaders_rc=$?
mkdir -p $O/tmp; FREE=5717540712448
for f in $FREE 5518700000000 5518750000000; do echo "dp preflight free=$f: $(TMPDIR=$O/tmp $PY $I/test/tdp.py $f $K/b/dp.py preflight $K $O/tmp 300000000000 2>&1 | tail -n 2 | tr '\n' ' ' | grep -o '"status": "[A-Z]*"\|"code": "[A-Z_]*"\|"plan_bytes": [0-9]*\|"margin_bytes": -*[0-9]*\|EXIT [0-9]*' | tr '\n' ' ')"; done
echo "dp control 7e23bbdd: $(TMPDIR=$O/tmp $PY $I/test/tdp.py $FREE $K/b/dp.py preflight $W/w34/n_go $O/tmp 300000000000 2>&1 | tail -n 2 | tr '\n' ' ' | grep -o '"code": "[A-Z_]*"\|"plan_bytes": [0-9]*\|"margin_bytes": -*[0-9]*\|EXIT [0-9]*' | tr '\n' ' ')"
for v in v_100_200 v_100_200_guard7; do echo "dp train $v: $($PY $I/test/tdp.py $FREE $K/b/dp.py train $K - 0 $I/test/$v.json $O/tree35/new 2>&1 | tail -n 2 | tr '\n' ' ' | grep -o '"status": "[A-Z]*"\|"code": "[A-Z_]*"\|"plan_bytes": [0-9]*\|"margin_bytes": -*[0-9]*\|EXIT [0-9]*' | tr '\n' ' ')"; done
$PY $I/test/til.py $K/b/il.py $O/til > $O/til.json 2>&1; echo til_rc=$?; $PY -c "import json,sys;d=json.load(open(sys.argv[1]));print({k:(v if isinstance(v,int) else v[0]) for k,v in d.items() if k!='ok_links'})" $O/til.json
timeout 400 bash $I/test/t_jn8.sh $I/jn/jn8.sh $O/jn8 > $O/jn8.log 2>&1; echo jn8_rc=$?; grep '^==' $O/jn8.log
timeout 400 bash $I/test/t_jn8.sh $I/jn/jn7.sh $O/jn7 > $O/jn7.log 2>&1; echo jn7_rc=$?; grep '^==' $O/jn7.log
$PY $I/test/tmet.py $K/b $O/tmet > $O/tmet.json 2>&1; echo tmet_rc=$?; tr -d '\n ' < $O/tmet.json | cut -c1-400; echo
for c in "new 607.9" "new 1900" "old 1200"; do set -- $c; timeout 300 $PY $I/test/tto.py $O/tree35/$1 $1 $2 2>&1 | tail -n 1 | cut -c1-260; done
cp $K/SHA256SUMS.txt $O/SHA256SUMS.txt; sha256sum $K/SHA256SUMS.txt
tar cf - --exclude=nsB --exclude=otherB --exclude=til --exclude=jn8 --exclude=jn7 --exclude=tmp --exclude=n_go --exclude=tree35 --exclude=tmet $LB </dev/null | ssh -o ConnectTimeout=20 trinity-3-30.ib 'mkdir -p /scratch/jjyeung/orch_n30/tree_rebuild29/work/fix21/rd/t18b && cd /scratch/jjyeung/orch_n30/tree_rebuild29/work/fix21/rd/t18 && tar xf - && echo GOT_RD'
echo END $(date -u +%TZ)

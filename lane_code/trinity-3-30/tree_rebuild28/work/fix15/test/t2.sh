# Trinity test 2 on trinity-1-18: (a) the stop-test run of test 1 (stop.sh was called without A15_JOB) ended by its own budget?
# (b) stop.sh test done right; (c) budget test again with the fixed proof. Run as bash -s.
set -u; export TZ=UTC
echo "host $(hostname -s) $(date -u +%TZ)"; [[ "$(hostname -s)" == trinity ]] && exit 9
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; KIT=$W/w33n/n_go; VENV=/scratch/jjyeung/envs/p1cpu
JOB=990015; D=/tmp/a15_rh_$JOB; Q=/tmp/q_22c714e1_$JOB
UV=$(readlink -f $VENV/bin/python3.12); UV=${UV%/bin/*}
echo "== (a) test-1 stop-test run"; tail -n 7 $D/stop.out | cut -c1-200; echo "left: [$(ps -u $(id -u) -o pid=,args= | grep -F $D | grep -v grep | cut -c1-120)]"
cd $D && base64 -d <<'B64' | tar xzf -
@@PAYLOAD@@
B64
echo "rh now: $(sha256sum rh/* | cut -c1-12 | tr '\n' ' ')"
E="A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_TEST_BINDS=$VENV:$UV:$KIT"
echo "== (b) stop.sh on sleeping ranks"
( env A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" A15_DRY=sleep A15_HARD_S=240 \
    nice -n 10 timeout -k 20 300 bash $D/rh/go.sh > $D/stop2.out 2>&1 ) &
sleep 40; A15_JOB=$JOB bash $D/rh/stop.sh 2>&1 | cut -c1-300; sleep 20; tail -n 9 $D/stop2.out | grep -v Terminated | cut -c1-300
echo "left after (b): [$(ps -u $(id -u) -o pid=,args= | grep -F $D | grep -v grep | cut -c1-120)]"
echo "== (c) budget 45 s"
env A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" A15_DRY=sleep A15_HARD_S=45 \
    nice -n 10 timeout -k 20 200 bash $D/rh/go.sh > $D/budget2.out 2>&1; echo "go rc=$?"; grep -v Terminated $D/budget2.out | tail -n 8 | cut -c1-300
echo "left after (c): [$(ps -u $(id -u) -o pid=,args= | grep -F $D | grep -v grep | cut -c1-120)]"
echo "== host job folder p: $(ls $Q/p | tr '\n' ' ') v.json $(sha256sum < $Q/v.json | cut -c1-16)"
du -sh $D $Q; date -u +%TZ

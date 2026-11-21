# Trinity test on trinity-1-18 (no GPU): fake job folder, then the driver up to the GPU need. Run as bash -s.
set -u; export TZ=UTC
echo "host $(hostname -s) $(date -u +%TZ)"; [[ "$(hostname -s)" == trinity ]] && exit 9
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; KIT=$W/w33n/n_go; VENV=/scratch/jjyeung/envs/p1cpu
JOB=990015; D=/tmp/a15_rh_$JOB; Q=/tmp/q_22c714e1_$JOB
sha256sum $KIT/SHA256SUMS.txt $KIT/k/j.json | cut -c1-16; ls -d $VENV /scratch/jjyeung/uv-python; which bwrap; bwrap --version
[[ -e $D || -e $Q ]] && { echo "test folders exist already: $D $Q"; ls -la $D $Q | head; exit 3; }
mkdir -p $D && chmod 700 $D && cd $D && base64 -d | tar xzf - && ls $D $D/rh | tr '\n' ' '; echo
nice -n 10 $VENV/bin/python -I -B $D/test/mkfake.py $KIT $Q $VENV || exit 4
UV=$(readlink -f $VENV/bin/python3.12); UV=${UV%/bin/*}
run() {  # $1 label; rest env
    local label=$1; shift
    echo "=== $label $(date -u +%TZ)"
    env "$@" A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" \
        nice -n 10 timeout -k 20 300 bash $D/rh/go.sh > $D/$label.out 2>&1; echo "go rc=$?"
    tail -n 40 $D/$label.out | cut -c1-600
    R=$(readlink -f $D/last); echo "run $R"
    for f in $R/log/ev_rank*.jsonl; do echo "-- $f"; cut -c1-900 $f; done
    echo "-- t.log tail"; tail -n 15 $R/log/t.raw.log 2>/dev/null | cut -c1-400
    echo "-- scratch upper"; (cd $R/w && find . -maxdepth 4 -newer $R/log/go.log -o -maxdepth 4 -type f -size -2k -print 2>/dev/null | head -40)
    echo "-- summary"; head -c 2500 $R/summary.json 2>/dev/null; echo
}
run dry A15_DRY=1 A15_HARD_S=240
echo "=== job folder untouched? (fake) p/rv.json p/pr.json present on host: $(ls $Q/p/rv.json $Q/p/pr.json 2>&1 | tr '\n' ' ')"; sha256sum $Q/v.json
echo "=== stop test: ranks that sleep, stopped by stop.sh"
( env A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" A15_DRY=sleep A15_HARD_S=240 \
    nice -n 10 timeout -k 20 300 bash $D/rh/go.sh > $D/stop.out 2>&1 ) &
sleep 45; bash $D/rh/stop.sh; sleep 20; echo "-- stop.out tail"; tail -n 14 $D/stop.out | cut -c1-400
echo "=== budget test: ranks that sleep, the driver's own budget (60 s) stops them"
env A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" A15_DRY=sleep A15_HARD_S=60 \
    nice -n 10 timeout -k 20 200 bash $D/rh/go.sh > $D/budget.out 2>&1; echo "go rc=$?"; tail -n 12 $D/budget.out | cut -c1-400
echo "=== left: $(ps -u $(id -u) -o pid,args | grep -F $D | grep -v grep | head -5)"
du -sh $D $Q; date -u +%TZ

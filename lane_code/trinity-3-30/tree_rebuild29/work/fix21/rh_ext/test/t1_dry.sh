# Test 1 (trinity-3-30, CPU only): fix15 test 4's dry run with the extended rh on a fresh fake job folder
# (kit 7e23bbdd copy fix15/kit34/n_go): the layout, the stand-in acceptance, the launch line on four CPU ranks to
# the tree's authenticate(), then the new planner step (up.py in the sandbox with --unshare-net) over the
# empty sink, then pre.sh. usage: bash t1_dry.sh <job number 9900xx> [kit]
set -u; export TZ=UTC
echo "host $(hostname -s) $(date -u +%TZ)"; [[ "$(hostname -s)" == trinity ]] && exit 9
E=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix21/rh_ext; KIT=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix15/kit34/n_go
VENV=/scratch/jjyeung/envs/p1cpu
KIT=${2:-$KIT}; JOB=${1:?job}; D=/tmp/a15_rh_$JOB; Q=/tmp/q_22c714e1_$JOB
UV=$(readlink -f $VENV/bin/python3.12); UV=${UV%/bin/*}
[[ -e $D || -e $Q ]] && { echo "exists: $D $Q"; exit 3; }
mkdir -p $D && chmod 700 $D && cp -a $E/rh $D/rh && mkdir $D/test && cp -p $E/test/mkfake.py $D/test/ && cd $D
echo "kit: $(sha256sum < $KIT/SHA256SUMS.txt | cut -c1-16) j.json $(sha256sum < $KIT/k/j.json | cut -c1-16)"; echo "rh: $(sha256sum rh/* | cut -c1-12 | tr '\n' ' ')"
nice -n 10 $VENV/bin/python -I -B $D/test/mkfake.py $KIT $Q $VENV | tail -1
env A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" A15_DRY=1 A15_HARD_S=300 \
    nice -n 10 timeout -k 20 360 bash $D/rh/go.sh > $D/dry.out 2>&1; echo "go rc=$?"; grep -v Terminated $D/dry.out | cut -c1-400
R=$(readlink -f $D/last); grep -h DRY_DONE $R/log/ev_rank*.jsonl | cut -c1-200
echo "== planner (empty sink)"; cat $R/log/plan.rc 2>/dev/null; cut -c1-1500 $R/log/plan.log 2>/dev/null
/usr/bin/python3 -I -c 'import json,sys; s=json.load(open(sys.argv[1])); print(json.dumps({k:s.get(k) for k in ("result","ranks_up","save_done_ranks","sink_bytes","sink_cleared","planner","planner_rc","errors")})[:2500])' $R/summary.json
echo "== pre.sh"; sed -i "s#Q_KIT=\${Q_KIT:-/project/community/jjyeung/okh7/x_22c714e1/n}#Q_KIT=\${Q_KIT:-$KIT}#" $D/rh/pre.sh
env A15_JOB=$JOB A15_TEST=1 A15_TEST_BINDS="$VENV $UV $KIT" nice -n 10 timeout 120 bash $D/rh/pre.sh 2>&1 | cut -c1-200
echo "left: [$(ps -u $(id -u) -o pid=,args= | grep -F $D | grep -v grep | cut -c1-120)]"; date -u +%TZ
echo "== launch args"; grep -o '"/tmp/q_22c714e1/p", "/tmp/q_22c714e1/v.json"' $R/log/t.raw.log | head -1; grep -h CHECKED $R/log/ev_rank0.jsonl | cut -c100-260
echo "== host fake p: $(ls $Q/p | tr '\n' ' ')"

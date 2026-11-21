# Trinity test 4 on trinity-1-18 (kit 7e23bbdd layout): the rh for 174246 (sha prefixes below) on a fresh fake job folder: dry run to the GPU need, then pre.sh.
set -u; export TZ=UTC
echo "host $(hostname -s) $(date -u +%TZ)"; [[ "$(hostname -s)" == trinity ]] && exit 9
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; KIT=$W/w34/n_go; VENV=/scratch/jjyeung/envs/p1cpu
JOB=990035; D=/tmp/a15_rh_$JOB; Q=/tmp/q_22c714e1_$JOB
UV=$(readlink -f $VENV/bin/python3.12); UV=${UV%/bin/*}
[[ -e $D || -e $Q ]] && { echo "exists: $D $Q"; exit 3; }
mkdir -p $D && chmod 700 $D && cd $D && base64 -d <<'B64' | tar xzf -
@@PAYLOAD@@
B64
echo "kit: $(sha256sum < $KIT/SHA256SUMS.txt | cut -c1-16) j.json $(sha256sum < $KIT/k/j.json | cut -c1-16)"; echo "rh: $(sha256sum rh/* | cut -c1-12 | tr '\n' ' ')"
nice -n 10 $VENV/bin/python -I -B $D/test/mkfake.py $KIT $Q $VENV | tail -1
env A15_JOB=$JOB A15_TEST=1 A15_KIT=$KIT A15_JOB_START=$(date +%s) A15_TEST_BINDS="$VENV $UV $KIT" A15_DRY=1 A15_HARD_S=200 \
    nice -n 10 timeout -k 20 260 bash $D/rh/go.sh > $D/dry.out 2>&1; echo "go rc=$?"; grep -v Terminated $D/dry.out | cut -c1-260
R=$(readlink -f $D/last); grep -h DRY_DONE $R/log/ev_rank*.jsonl | cut -c1-200
echo "== pre.sh"; sed -i "s#Q_KIT=\${Q_KIT:-/project/community/jjyeung/okh7/x_22c714e1/n}#Q_KIT=\${Q_KIT:-$KIT}#" $D/rh/pre.sh
env A15_JOB=$JOB A15_TEST=1 A15_TEST_BINDS="$VENV $UV $KIT" nice -n 10 timeout 120 bash $D/rh/pre.sh 2>&1 | cut -c1-200
echo "left: [$(ps -u $(id -u) -o pid=,args= | grep -F $D | grep -v grep | cut -c1-120)]"; date -u +%TZ
R=$(readlink -f $D/last); echo "== launch args"; grep -o '"/tmp/q_22c714e1/p", "/tmp/q_22c714e1/v.json"' $R/log/t.raw.log | head -1; grep -h CHECKED $R/log/ev_rank0.jsonl | cut -c100-260
echo "== host fake p: $(ls $Q/p | tr '\n' ' ')"

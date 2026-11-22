# Resume test (trinity-3-30, CPU only, gloo): A (dying allocation) -> publisher stand-in -> rs.py stage on a new
# run folder -> B (resumed allocation: load, one more step, one save). Each phase runs in bwrap with the whole host
# read-only except its own run folder, no network, the run folder bound at the fixed namespace NS.
# usage: bash run.sh <label> [world]
set -u; export TZ=UTC
echo "host $(hostname -s) $(date -u +%TZ)"; [[ "$(hostname -s)" == trinity ]] && exit 9
W=/scratch/jjyeung/orch_n30/tree_rebuild30/work/resume36; PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=${1:?label}; WORLD=${2:-4}; NS=/tmp/q_rs36; T=$W/rd/$L
mkdir -p $T || exit 1; [[ -z "$(ls -A $T)" ]] || { echo "label used"; exit 1; }
KIT=$W/kit/n_go
sb() {  # sb <run folder> <job id> cmd...
    local R=$1 J=$2; shift 2
    mkdir -p $R/tmp $R/cache
    nice -n 10 timeout -k 10 900 /usr/bin/bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /dev/shm --tmpfs /tmp \
        --bind $R $NS --bind $T/log $T/log --unshare-net --unshare-user --die-with-parent \
        --setenv TMPDIR $NS/tmp --setenv XDG_CACHE_HOME $NS/cache --setenv HOME $NS/tmp --setenv HF_HOME $NS/cache/hf \
        --setenv TORCH_HOME $NS/cache/torch --setenv TRITON_CACHE_DIR $NS/cache/triton --setenv MPLCONFIGDIR $NS/cache/mpl \
        --setenv PYTHONNOUSERSITE 1 --setenv PYTHONDONTWRITEBYTECODE 1 --setenv OMP_NUM_THREADS 1 --setenv GLOO_SOCKET_IFNAME lo \
        --setenv RS_WORLD $WORLD --setenv RS_NS $NS --setenv SLURM_JOB_ID $J --setenv PYTHONPATH $W/tree \
        "$@"
}
mkdir -p $T/log
for v in A:same B:same Bx:other Bc:same; do
    $PY -B -s $W/test/fx_job.py $W $T/${v%%:*} $NS ${v##*:} > $T/log/fx_${v%%:*}.log 2>&1 || { echo "fx ${v%%:*} failed"; cat $T/log/fx_${v%%:*}.log; exit 1; }
done
cmp $T/A/v.json $T/B/v.json && echo "v.json A == B (same config bytes, same preparation pin)"
cmp -s $T/A/v.json $T/Bx/v.json || echo "v.json A != Bx (host receipt variant: other preparation pin)"
echo "== A: dying allocation 174444 ($WORLD gloo ranks)"; t=$(date +%s)
sb $T/A 174444 $PY -B -s $W/test/t_resume.py A $T/log > $T/log/A.log 2>&1; echo "A rc=$? in $(( $(date +%s) - t )) s"; tail -n 3 $T/log/A.log | cut -c1-300
echo "== publisher stand-in (local parts + receipt + card)"
$PY -B -I -s $W/test/pub.py $T/A $NS $T/durable $T/card.json 174444 > $T/log/pub.log 2>&1; echo "pub rc=$?"; cut -c1-600 $T/log/pub.log
$PY -B -I -s - $T/card.json $T/card_badpart.json <<'EOF'
import json, sys
c = json.load(open(sys.argv[1])); c['parts'][2]['sha256'] = 'f' * 64
open(sys.argv[2], 'w').write(json.dumps(c, indent=1, sort_keys=True) + '\n')
EOF
for v in B Bx Bc; do
    card=$T/card.json; [[ $v == Bc ]] && card=$T/card_badpart.json
    echo "== rs.py stage on run $v (kit $KIT/b/rs.py, card $(basename $card))"
    sb $T/$v 990036 $PY -B -s $KIT/b/rs.py $W/tree $NS/v.json $card $NS/rs_ok.json $NS/live_spool/state > $T/log/rs_$v.log 2>&1
    echo "rs $v rc=$?"; tail -n 1 $T/log/rs_$v.log | cut -c1-700
done
echo "== B: resumed allocation 990036 ($WORLD gloo ranks)"; t=$(date +%s)
sb $T/B 990036 $PY -B -s $W/test/t_resume.py B $T/log > $T/log/B.log 2>&1; echo "B rc=$? in $(( $(date +%s) - t )) s"; tail -n 3 $T/log/B.log | cut -c1-300
echo "== results"
$PY -B -I -s $W/test/check.py $T $WORLD

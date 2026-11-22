# Test 2 (trinity-3-30, CPU only): the rehearsal's save part and planner on the tree's tiny fixture model.
# Both steps run in bwrap with the whole host read-only except the test folder, and without network.
# usage: bash t2_save.sh <tree dir (the kit's extracted tree)> [kit] [world]
set -u; export TZ=UTC
echo "host $(hostname -s) $(date -u +%TZ)"; [[ "$(hostname -s)" == trinity ]] && exit 9
E=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix21/rh_ext; KIT=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix15/kit34/n_go
PY=/scratch/jjyeung/envs/p1cpu/bin/python; TREE=${1:?tree}; KIT=${2:-$KIT}; JOB=990061; W=${3:-2}
T=$E/rd/t2_$(date -u +%Y%m%dT%H%M%SZ); mkdir -p $T/tmp $T/cache $T/log $T/pc; echo "out $T"
SB=(/usr/bin/bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /dev/shm --bind $T $T --unshare-net --unshare-user --die-with-parent
    --setenv TMPDIR $T/tmp --setenv XDG_CACHE_HOME $T/cache --setenv HF_HOME $T/cache/hf --setenv TORCH_HOME $T/cache/torch
    --setenv TRITON_CACHE_DIR $T/cache/triton --setenv MPLCONFIGDIR $T/cache/mpl --setenv HOME $T/tmp
    --setenv PYTHONNOUSERSITE 1 --setenv PYTHONDONTWRITEBYTECODE 1 --setenv OMP_NUM_THREADS 2 --setenv GLOO_SOCKET_IFNAME lo
    --setenv Q_KIT $KIT --setenv A15_T2_WORLD $W --setenv A15_RUN $T --setenv A15_LOG $T/log --setenv TK_JOB_START "$(date +%s)")
echo "== save part (sx.save_export, $W gloo ranks, kit $KIT)"
t=$(date +%s)
nice -n 10 timeout -k 10 900 "${SB[@]}" --setenv PYTHONPATH "$TREE:$E/rh" $PY -B -s $E/test/t2_save.py $T $KIT > $T/save.log 2>&1; echo "save rc=$? in $(( $(date +%s) - t )) s"
tail -n 5 $T/save.log | cut -c1-400
echo "== planner (up.py: kit pc.py Copier pass, writer sw.py)"
t=$(date +%s)
nice -n 10 timeout -k 10 300 "${SB[@]}" $PY -B -I -s $E/rh/up.py $T/sink $T/pc $JOB > $T/log/plan.log 2>&1; echo "planner rc=$? in $(( $(date +%s) - t )) s"
cut -c1-2500 $T/log/plan.log
echo "== results"
$PY -I -B $E/test/t2_check.py $T $KIT

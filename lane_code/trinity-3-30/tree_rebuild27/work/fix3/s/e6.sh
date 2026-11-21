W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u
mkdir -p $W/w27fix/work $W/w27fix/src
echo "--- m400real"; find $W/ext/m400real -maxdepth 4 | head -40
echo "--- preceipts"; find $W/ext/preceipts -maxdepth 2 | head -30
echo "--- p_runtime"; find $W/inputs/p_runtime -maxdepth 2 | head -30
echo "--- ns tools"; which bwrap unshare 2>&1; cat /proc/sys/user/max_user_namespaces
timeout 20 unshare -Urm sh -c 'mount -t tmpfs none /tmp && mkdir -p /tmp/q_22c714e1 && echo UNSHARE_OK $(id -u)' 2>&1 | tail -2
echo "--- tree_r1 top"; ls $W/w24w/work/tree_r1 | head -40
echo "--- kit tree tar top"; tar tf $W/w26fix2/n_go/k/t_e047002134f979bd.tar | cut -d/ -f1 | sort | uniq -c
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
PY="nice -n 10 timeout 300 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"
cd $W/w27fix/work
$PY -c "
import sys
sys.path.insert(0,'$W/w26fix/tree'); sys.path.append('$W/w24w/work/tree_r1')
try:
    import student_pilot.carrier_c1_run as c; print('IMPORT carrier_c1_run OK', c.__file__)
    import launch_r1.p_opener_witness as w; print('IMPORT witness OK', w.__file__)
    import trace_format; print('trace_format from', trace_format.__file__)
    import transformers, torch; print('transformers', transformers.__version__, 'torch', torch.__version__)
except Exception as e:
    import traceback; traceback.print_exc()
" 2>&1 | tail -12

W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
T=$W/w26fix/tree; K=$W/w26fix/n_go
cd $T
echo "==== host_environment / begin_host"; L=$(grep -n "def host_environment" launch_r1/entry.py | cut -d: -f1); echo L=$L; sed -n "$((L-3)),$((L+45))p" launch_r1/entry.py
echo "==== state grep"; grep -rn "ContextVar(\|^ *global \|os\.environ\[.*\] *=\|os\.environ\.update\|putenv\|set_num_threads\|tempfile\.tempdir\|os\.chdir\|os\.umask\|setrlimit\|signal\.signal\|set_default_dtype\|allow_tf32\|use_deterministic\|cudnn\.benchmark" --include=*.py launch_r1 student_pilot | grep -v "/tests\?/" | head -80
echo "==== a.py callers"; grep -n "a\.py\|python" $K/b/q.sh $K/job.sh $K/b/e.sh 2>/dev/null | head -30
echo "==== envs"; for e in /scratch/jjyeung/envs/*/; do p=$e/bin/python; [ -x $p ] && echo "$e $($p -c 'import sys;print(sys.version.split()[0])' 2>&1) torch=$(ls -d $e/lib/python3*/site-packages/torch 2>/dev/null | head -1)"; done
echo "==== top of tree"; ls $T; ls $T/student_pilot | wc -l; head -5 $T/student_pilot/__init__.py $T/launch_r1/__init__.py 2>&1

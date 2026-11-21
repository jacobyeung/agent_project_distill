F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix; RUN=$F/work/${1:-sim2}
date -u +%TZ; tmux has-session -t w28b 2>/dev/null && echo RUNNING || echo FINISHED
cat $F/work/cpu2.out | cut -c1-300
/scratch/jjyeung/envs/p1cpu/bin/python -I $F/src/sum.py $RUN/r.txt 60 2>&1 | cut -c1-2300
echo "-- stderr tail"; tail -25 $RUN/e.txt | cut -c1-400

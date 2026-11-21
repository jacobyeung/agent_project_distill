F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix; RUN=$F/work/sim4
date -u +%TZ; tmux has-session -t w28d 2>/dev/null && echo RUNNING || echo FINISHED
cat $F/work/cpu4.out | cut -c1-260
/scratch/jjyeung/envs/p1cpu/bin/python -I $F/src/sum.py $RUN/r.txt 60 2>&1 | cut -c1-2600 | grep -v "^   mark\|^rc " | head -150
echo "-- stderr tail"; tail -6 $RUN/e.txt | cut -c1-300

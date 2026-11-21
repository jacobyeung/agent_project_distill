X=/project/community/jjyeung/okh7/x_22c714e1
date -u +%TZ
M=/project/community/jjyeung/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots
echo "--- snapshot"; ls -la $M 2>&1 | head; ls -la $M/* 2>&1 | head -20
echo "--- X/w/t"; ls $X/w 2>&1 | head; ls $X/w/t 2>&1 | head -30
echo "--- X top dirs"; ls -d $X/s27fix $X/s28fix $X/n $X/t_* 2>&1 | head
echo "--- jn6 / j.sh"; ls -la $X/*.sh $X/n/job.sh 2>&1 | head; ls $X/r 2>&1 | head -20
echo "--- how the job was launched: Q_ROOT, Q_NS"; grep -n "Q_ROOT=\|Q_NS=\|Q_KIT=\|PILOT_VENV=\|TK_JOBDIR=\|sbatch\|#SBATCH" $X/jn6.sh 2>/dev/null | cut -c1-260 | head -40
ls -la $X | head -80
sinfo -p advanced -o "%P %a %l %D %t %G" 2>&1 | head -8
df -h /project/community | tail -1

export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -j 174134 -h -o "%i %T %M %N %b %C %m"
echo ==== WRAPPER; wc -c $X/jn7.sh; cat $X/jn7.sh
echo ==== NODE
timeout 120 srun --overlap --jobid 174134 -N1 -n1 bash -c '
Q=/tmp/q_22c714e1_174134
echo "-- ps"; ps -u $(id -un) -o pid,ppid,etime,stat,args --width 250 | head -40
W=$(pgrep -u $(id -un) -f "jn7|slurm_script" | head -1); echo "wrapper pid candidates: $(pgrep -u $(id -un) -f "jn7|slurm_script" | tr "\n" " ")"
for p in $(pgrep -u $(id -un) -f "jn7|slurm_script" | head -3); do echo "-- environ $p"; tr "\0" "\n" < /proc/$p/environ | grep -E "^(Q_|TK_|SLURM_JOB_ID|SLURM_JOB_GPUS|SLURM_STEP_GPUS|SLURM_GPUS|CUDA_VISIBLE|R1_|PATH=|TMPDIR|HOME=|SLURM_CPUS|SLURM_MEM)" ; done
echo "-- my step env"; env | grep -E "^(CUDA_VISIBLE|SLURM_STEP_GPUS|SLURM_JOB_GPUS|SLURM_GPUS|SLURM_CPUS|SLURM_STEP_ID)"
echo "-- gpus"; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1 | head -12; nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>&1 | head
echo "-- dirs"; for d in x x/b x/k x/o x/runs j j/* s s/aws s/c7d31ddd rp tmp o live_spool cache; do echo "[$d] $(ls -A $Q/$d 2>/dev/null | head -30 | tr "\n" " ")"; done
echo "-- kit 0.json"; python3 -I -B - <<PY
import json,glob,os
for f in glob.glob("/project/community/jjyeung/okh7/*/k/0.json")[:6]: print(f, os.path.getsize(f))
PY
free -g | head -2; nproc; uptime; df -h /tmp | tail -1; uname -r; cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null; cat /proc/sys/user/max_user_namespaces
'

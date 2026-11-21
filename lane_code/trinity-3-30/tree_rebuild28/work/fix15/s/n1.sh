export TZ=UTC; date -u +%TZ
squeue -j 174198 -h -o '%T|%M|%N' 2>&1
timeout 100 srun --overlap --jobid 174198 -N1 -n1 bash -c '
Q=/tmp/q_22c714e1_174198; echo "host $(hostname -s) kernel $(uname -r)"
echo "== top"; ls -la $Q | cut -c1-140 | head -60
for d in p p/q j h rp x cache; do echo "== $d"; ls -la $Q/$d 2>&1 | cut -c1-140 | head -40; done
echo "== /tmp/jjyeung"; ls -la /tmp/jjyeung 2>&1 | head; ls -ld /tmp/q_22c714e1 2>&1
CUR=$Q/h/k/0.json; BW=$(/usr/bin/python3 -B -I -c "import json,sys;print(json.load(open(sys.argv[1]))[\"bwrap\"][\"file\"])" $CUR 2>&1); echo "bwrap=$BW"; $BW --version 2>&1; $BW --help 2>&1 | grep -i overlay | head -5
cat /proc/sys/user/max_user_namespaces 2>&1; cat /proc/sys/kernel/unprivileged_userns_clone 2>&1 | head -1
T=/tmp/a15_rh_174198/ovt; mkdir -p $T/lo $T/up $T/wk $T/m && echo x > $T/lo/a && \
 $BW --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --bind $T $T --overlay-src $T/lo --overlay $T/up $T/wk $T/m --unshare-user bash -c "echo y > $T/m/b && cat $T/m/a" 2>&1 | head -3; echo "overlay_rc=$? up=$(ls $T/up 2>&1 | tr "\n" " ") lo=$(ls $T/lo | tr "\n" " ")"
grep -w overlay /proc/filesystems
echo "== df"; df -h /tmp /dev/shm | tail -2; free -g | sed -n 2p; nproc
echo "== gpus"; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader; nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
echo "CVD=${CUDA_VISIBLE_DEVICES:-unset} SLURM_STEP_GPUS=${SLURM_STEP_GPUS:-} SLURM_JOB_GPUS=${SLURM_JOB_GPUS:-}"
echo "== listen"; (ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null) | awk "NR>1{print \$4}" | sort | tr "\n" " " | cut -c1-1500; echo
echo "== procs"; ps -u $(id -u) -o pid,ppid,etime,pcpu,rss,args --width 200 | grep -v -E "ps -u|grep|cut" | cut -c1-200 | head -40
echo "== cgroup"; cat /proc/self/cgroup | head -5
for f in memory.current memory.max memory.limit_in_bytes memory.usage_in_bytes; do for c in /sys/fs/cgroup/memory/slurm/uid_$(id -u)/job_174198 /sys/fs/cgroup/system.slice/slurmstepd.scope/job_174198; do [ -e $c/$f ] && echo "$c/$f $(cat $c/$f)"; done; done
tail -n 8 $Q/174198.steps 2>&1 | cut -c1-200
'
echo srun_rc=$?
date -u +%TZ

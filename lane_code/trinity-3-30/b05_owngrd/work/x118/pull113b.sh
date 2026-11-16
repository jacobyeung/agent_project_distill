S=/dev/shm/jjyeung/b05; tail -2 $S/teacher_k1/worker_1.log; ls $S/teacher_k1/*/DONE.json | wc -l; grep -c '"event": "failed"' $S/teacher_k1/PROGRESS.*.jsonl; grep shard_complete $S/teacher_k1/PROGRESS.*.jsonl | wc -l
cd $S && tar cf - teacher_k1 | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full && cd /scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full && tar xf -"; echo pull_rc=$?
nvidia-smi -i 2,3 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; tmux ls | grep b05

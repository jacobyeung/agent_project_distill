timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
date -u +%TZ; hostname -s; ps -u jjyeung --no-headers | wc -l; df -h /scratch | tail -1
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "; echo; echo "apps: $(nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l)"
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/ 2>/dev/null | grep -m1 INBOX_FROM_NONTRAINING
cd /scratch/jjyeung/orch_n30/sb_cachk && tmux new-session -d -s sb_carry "OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash kit_v2/launch_gpu.sh > /scratch/jjyeung/orch_n30/sb_cachk/out/v2/LAUNCH_228.log 2>&1"
sleep 15; tmux ls; tail -5 /scratch/jjyeung/orch_n30/sb_cachk/out/v2/LAUNCH_228.log; ls /scratch/jjyeung/orch_n30/sb_cachk/out/v2/track 2>/dev/null | head
Y

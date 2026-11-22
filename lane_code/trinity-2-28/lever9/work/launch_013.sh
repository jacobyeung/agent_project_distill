hostname -s; date -u +%FT%TZ
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
tmux has-session -t j1_gpu 2>/dev/null && { echo "j1_gpu session exists; not launching"; exit 1; }
cd /scratch/jjyeung/orch_n30/lever8/j1 || exit 1
ls out; [ -e out/detect/KILLED ] && { echo KILLED exists; exit 1; }
df -h /scratch | tail -1
tmux new-session -d -s j1_gpu "bash kit/launch_gpu.sh" && echo launched
sleep 20; tail -5 out/detect/EVENTS.jsonl 2>&1

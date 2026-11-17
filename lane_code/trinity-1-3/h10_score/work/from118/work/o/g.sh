export TZ=UTC; date -u +%T
timeout 60 srun --jobid=170631 --overlap -n1 -c1 --mem=1G --gres=gpu:1 nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader 2>&1 | head -3
timeout 60 srun --jobid=170631 --overlap -n1 -c1 --mem=1G --gres=none bash -c 'ls /tmp/a170631b01ec87a6f29b/sj/b01ec87a6f29b/r/ /tmp/a170631b01ec87a6f29b/sj/b01ec87a6f29b/r/logs 2>&1; tail -c 1500 /tmp/a170631b01ec87a6f29b/sj/b01ec87a6f29b/r/logs/1.log 2>/dev/null' 2>&1 | head -40

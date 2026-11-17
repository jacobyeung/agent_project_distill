export TZ=UTC; date -u +%T
R=/tmp/a170631b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170631 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; ls $R $R/logs $R/metadata; find $R/metadata/journals -name items.jsonl -exec wc -l {} \; 2>/dev/null; tail -c 1200 $R/logs/1.log" 2>&1 | head -60

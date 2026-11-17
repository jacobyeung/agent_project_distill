export TZ=UTC; date -u +%FT%TZ
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 40 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; wc -l < $R/metadata/journals/3/0/items.jsonl; tail -n1 $R/logs/30.log | cut -c1-150" 2>&1 | tail -4
for d in /project/community/jjyeung/okh7 /project/community/jjyeung; do ls -d $d/x_07ca49df* 2>/dev/null; done
ls /project/community/jjyeung/okh7 | head -50 | tr '\n' ' '

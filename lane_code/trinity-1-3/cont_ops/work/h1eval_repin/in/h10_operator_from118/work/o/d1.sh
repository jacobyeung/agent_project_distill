export TZ=UTC; date -u +%FT%TZ
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; ls -la $R/logs; for f in $R/logs/*; do echo == \$f; tail -c 1500 \$f; echo; done; cut -c1-400 $R/metadata/journals/3/0/items.jsonl; ps -eo pid,etime,pcpu,rss,args --sort=-pcpu | head -8 | cut -c1-200" 2>&1 | head -150

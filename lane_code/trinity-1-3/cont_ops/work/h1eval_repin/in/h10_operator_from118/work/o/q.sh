export TZ=UTC; date -u +%FT%TZ
squeue -j 170674 -h -o '%i %T %M %N'
ls /project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ab2 | tr '\n' ' '; echo
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; for f in $R/metadata/journals/*/*/items.jsonl; do echo \$f \$(wc -l < \$f); done; tail -n 1 $R/logs/30.log | cut -c1-200; ls $R/logs; ps -o etime,pcpu -p \$(pgrep -f boot.py | head -1)" 2>&1 | tail -12

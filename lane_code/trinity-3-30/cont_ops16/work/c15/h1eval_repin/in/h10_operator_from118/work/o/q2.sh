export TZ=UTC; date -u +%FT%TZ
squeue -j 170694 -h -o '%i %T %M %N'
ls /project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ac6 | tr '\n' ' '; echo
R=/tmp/a170694b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170694 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "ls /tmp | grep a170694; ls $R $R/logs 2>&1 | tr \"\\n\" \" \"; echo; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; for f in $R/metadata/journals/*/*/items.jsonl; do echo \$f \$(wc -l < \$f); done; tail -n 1 $R/logs/4*.log | cut -c1-200; ls $R/logs; ps -o etime,pcpu -p \$(pgrep -f boot.py | head -1)" 2>&1 | tail -12

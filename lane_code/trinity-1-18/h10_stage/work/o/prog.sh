export TZ=UTC; date -u +%FT%TZ
squeue -j 170674 -h -o '%i %T %M %l %N'
ls -la /project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ab2 2>&1 | grep -v total | awk '{print $5,$9}' | tr '\n' ' '; echo
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader; for f in $R/metadata/journals/*/*/items.jsonl; do echo \$f \$(wc -l < \$f); done; tail -n 2 $R/STEPS.jsonl | cut -c1-250; grep -c '\"finish\": \"eos\"' $R/logs/0*.log 2>/dev/null; grep -h -o '\"finish\": \"[a-z_]*\"' $R/logs/0*.log | sort | uniq -c; grep -h projection $R/logs/[0-9][0-9].log | cut -c1-260; ls $R" 2>&1 | head -30

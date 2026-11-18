R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "tail -n 4 $R/logs/30.log | cut -c1-300" 2>&1 | head -8

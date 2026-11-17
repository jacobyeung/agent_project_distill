W=/project/community/jjyeung/okh7/e6fc152498; tail -n 4 $W/callcount.out | cut -c1-400; pgrep -u $USER -f callcount.py >/dev/null && echo RUNNING
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 40 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "wc -l < $R/metadata/journals/3/0/items.jsonl; tail -n2 $R/logs/30.log | cut -c1-150; tail -n2 $R/STEPS.jsonl | cut -c1-200" 2>&1 | tail -5

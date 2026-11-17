export TZ=UTC; date -u +%FT%TZ
R=/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r
timeout 40 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c "ls $R/metadata; [ -e $R/metadata/STOP ] || echo lane_h10_stage_rule_0627Z > $R/metadata/STOP; ls -la $R/metadata/STOP; cat $R/metadata/STOP; wc -l < $R/metadata/journals/3/0/items.jsonl" 2>&1 | tail -6

S=/dev/shm/jjyeung/b05; date -u; for i in 0 1; do echo "== $i"; grep -v -i warn $S/teacher_k1/worker_$i.log | tail -4 | cut -c1-300; done
ls $S/teacher_k1 | wc -l; ls $S/teacher_k1/*/DONE.json 2>/dev/null | wc -l; cat $S/teacher_k1/PROGRESS.*.jsonl 2>/dev/null | tail -2 | cut -c1-300
nvidia-smi -i 2,3 --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; du -sh $S/teacher_k1; tmux ls | grep b05

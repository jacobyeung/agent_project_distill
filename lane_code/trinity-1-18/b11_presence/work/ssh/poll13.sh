S=/dev/shm/jjyeung/b11_presence/lane
date -u +%T; tmux ls 2>&1 | grep b11
nvidia-smi -i 1 --query-gpu=memory.used,utilization.gpu --format=csv,noheader
tail -4 $S/work/logs/run_gpu.log; tail -c 1500 $S/work/logs/run_gpu.outer.log 2>/dev/null | tail -5
for f in det_a det_b scorer_full direct; do [ -f $S/work/logs/$f.log ] && { echo "== $f"; grep -v -i -E 'warn|fast path|Loading weights' $S/work/logs/$f.log | tail -4 | cut -c1-400; }; done
ls $S/out/det/det_a/V 2>/dev/null | wc -l; ls $S/out/journals/V 2>/dev/null | wc -l

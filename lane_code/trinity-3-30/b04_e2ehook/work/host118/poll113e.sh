L=/dev/shm/jjyeung/b04/host/b04_e2ehook; R=$L/parity_kit/host_results/cpu_first_c; T=$L/../tree_rebuild/work/base/tree_b01ce449
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=/dev/shm/jjyeung/b04/pyoverlay; SP=/dev/shm/jjyeung/b05/stage/sam3_capretry_native_v1/lib/python3.12/site-packages
grep -v "Warning\|warn" $L/work/first_c.log | tail -c 600; echo; tmux ls 2>/dev/null | grep b04
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-120; wc -l $R/items.jsonl
for p in wcwidth; do if PYTHONPATH=$OV $PY -c "import $p" 2>/dev/null; then echo "have $p"; else (cd $SP && tar cf - $p $p-*.dist-info 2>/dev/null) | tar xf - -C $OV && echo "copied $p"; fi; done
cd $L && PYTHONPATH=$OV timeout 120 $PY -B -m parity_kit.sam3_probe --source-root /dev/shm/jjyeung/b05/stage/sam3src --checkpoint /dev/shm/jjyeung/b05/stage/sam3.pt --tree $T 2>&1 | grep -A3 "missing\|ready"
ls /dev/shm/jjyeung/b05/stage/sam3src /dev/shm/jjyeung/b05/stage | grep -i -v '^[0-9a-f][0-9a-f]$' | head; ls /dev/shm/jjyeung/b05/lane/code/owngrd/vendor 2>/dev/null | head

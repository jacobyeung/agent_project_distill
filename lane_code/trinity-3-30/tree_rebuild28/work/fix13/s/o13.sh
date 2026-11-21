export TZ=UTC; date -u +%TZ
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_f13_174134; for f in t6 t5; do echo == $f; grep "^EV" log/$f.log | grep -v "LAYOUT\|preflight" | cut -c1-3000 | tail -6; done; ls -la --time-style=+%H:%M:%S live; ps -u $(id -un) -o pid,etime,pcpu,args --width 150 | grep -E "t1.py" | grep -v grep'

export TZ=UTC; date -u +%TZ
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_f13_174134; for f in t2 t3; do echo == $f; grep "^EV" log/$f.log | grep -v LAYOUT | cut -c1-2500 | tail -7; done; ps -u $(id -un) -o pid,etime,pcpu,args --width 150 | grep -E "t1.py" | grep -v grep; uptime'

export TZ=UTC; date -u +%TZ
nohup setsid srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134 && exec bash L.sh c.py /tmp/a15_dbg_174134/n1 > log/c1.log 2>&1' > /dev/null 2>&1 < /dev/null &
sleep 20
pgrep -u $(id -un) -af "srun --overlap --jobid 174134" | cut -c1-160
timeout 60 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; ls -la log n1 2>&1 | head -20; tail -c 3000 log/c1.log'
squeue -j 174134 -h -o "%i %T %M %N"

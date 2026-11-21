export TZ=UTC; date -u +%TZ
nohup setsid srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134 && exec bash L.sh post1.py /tmp/a15_dbg_174134/n2 /tmp/a15_dbg_174134/n2e b > log/post1.log 2>&1' > /dev/null 2>&1 < /dev/null &
sleep 20
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; echo "== post1"; tail -c 700 log/post1.log; echo; echo "== evb tail"; tail -n 4 n2/evb.jsonl | cut -c1-900; echo "== reader filters"; cat n2/p/q/bb/reader_filters.json | cut -c1-600; echo; ls -la n2/p/q/bb n2/p/q/hb | cut -c1-120'

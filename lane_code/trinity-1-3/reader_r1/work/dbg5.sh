export TZ=UTC; date -u +%FT%TZ
J=172456
timeout 100 srun --jobid=$J --overlap -n1 -c1 --mem=1G bash -c '
P=$(pgrep -f "boot.py -B -I 5.py 40.json" | head -1)
a=$(grep rchar /proc/$P/io | cut -d" " -f2); s=$(grep syscr /proc/$P/io | cut -d" " -f2); sleep 10; b=$(grep rchar /proc/$P/io | cut -d" " -f2); t=$(grep syscr /proc/$P/io | cut -d" " -f2)
echo "rchar/10s $(( (b-a)/1000000 )) MB, syscr $((t-s))"
for i in 1 2 3 4 5; do cat /proc/$P/syscall 2>&1 | cut -c1-60; cat /proc/$P/wchan; echo; sleep 0.5; done
wc -l /tmp/a'$J'*/sj/b01ec87a6f29b/r/metadata/reads/0/metadata/journals/4/0/items.jsonl
grep -c . /tmp/a'$J'*/sj/b01ec87a6f29b/r/metadata/reads/0/metadata/journals/4/0/worker.log
ls -la /proc/$P/cwd; readlink /proc/$P/exe
' 2>&1 | tail -20

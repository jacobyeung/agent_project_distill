export TZ=UTC; date -u +%FT%TZ
J=172456
squeue -j $J -h -o '%i %T %M'
timeout 90 srun --jobid=$J --overlap -n1 -c1 --mem=1G bash -c '
R=$(ls -d /tmp/a'$J'*/sj/b01ec87a6f29b/r); cd $R
ls metadata/reads/0/metadata/journals/ ; ls metadata/reads/0/metadata/journals/*/0/ | head -40
for f in metadata/reads/0/metadata/journals/*/0/progress.json; do echo "== $f"; head -c 400 $f; echo; done
for f in metadata/reads/0/metadata/journals/*/0/worker.log; do echo "== $f"; tail -5 $f | cut -c1-300; done
ls -la metadata/reads/0/logs/ logs/ | head -20
for f in metadata/reads/0/logs/*.log logs/*.log; do echo "== $f"; tail -4 $f | cut -c1-300; done
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
ps -eo pid,etime,pcpu,rss,args --sort=-pcpu | grep -v "ps -eo" | head -8 | cut -c1-200
' 2>&1 | tail -80

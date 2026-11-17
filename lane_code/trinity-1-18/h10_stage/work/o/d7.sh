export TZ=UTC; date -u +%FT%TZ
timeout 60 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c '
P=2445095; grep -E "VmRSS|VmHWM|VmPeak|VmSize|RssAnon" /proc/$P/status; free -g | head -2
for t in 2445095 2445476; do echo $t $(awk "{print \$14,\$15}" /proc/$P/task/$t/stat); done; sleep 5; for t in 2445095 2445476; do echo $t $(awk "{print \$14,\$15}" /proc/$P/task/$t/stat); done
grep -c . /proc/$P/maps' 2>&1 | head -20

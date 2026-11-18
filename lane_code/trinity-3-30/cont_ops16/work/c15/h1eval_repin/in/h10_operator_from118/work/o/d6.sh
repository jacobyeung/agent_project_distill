export TZ=UTC; date -u +%FT%TZ
timeout 110 srun --jobid=170674 --overlap -n1 -c1 --mem=1G --gres=gpu:1 bash -c '
P=2445095; cat /proc/sys/kernel/yama/ptrace_scope 2>&1; grep -E "^State" /proc/$P/status
timeout -s INT 70 gdb -nx -batch -iex "set auto-load off" -iex "set debuginfod enabled off" -ex "set pagination off" -ex "thread 1" -ex "bt 25" -p $P 2>&1 | grep -E "^#|Thread|ptrace|denied" | cut -c1-220 | head -40
sleep 1; grep -E "^State" /proc/$P/status
' 2>&1 | head -60

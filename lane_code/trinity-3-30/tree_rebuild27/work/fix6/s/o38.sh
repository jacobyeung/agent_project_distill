export TZ=UTC; date -u +%TZ
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; cat log/tr.log | tail -4; echo == train; wc -c log/train.log; grep -v -E "UserWarning|_cpu_device_warning|fast path|Loading weights" log/train.log | tail -c 9000'

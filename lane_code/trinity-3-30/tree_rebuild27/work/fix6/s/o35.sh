export TZ=UTC; date -u +%TZ
timeout 40 srun --overlap --jobid 174134 -N1 -n1 bash -c 'cd /tmp/a15_dbg_174134; cat log/tr.log | tail -3; echo == train; grep -v -E "UserWarning|_cpu_device_warning|fast path|Loading weights" log/train.log | tail -n 25 | cut -c1-500; echo; tail -n 4 log/smi_train.log; ls -la rp 2>&1 | head; echo == eva; grep -c . n2/eva.jsonl'
squeue -j 174134 -h -o "%i %T %M %N"

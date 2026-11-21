export TZ=UTC; date -u +%TZ
timeout 50 srun --overlap --jobid 174134 -N1 -n1 bash -c '
cd /tmp/a15_dbg_174134
echo "== tr2/log (read only)"; ls -la --time-style=+%H:%M:%S tr2/log tr/log | cut -c1-110
for f in tr2/log/*; do echo "---- $f ($(stat -c %s $f) B, mtime $(date -u -d @$(stat -c %Y $f) +%H:%M:%S))"; grep -v -E "UserWarning|_cpu_device_warning|fast path|Loading weights" "$f" | tail -c 1800 | cut -c1-400; echo; done 2>&1 | head -120
'

X=/project/community/jjyeung/okh7/x_22c714e1; echo "FS1 $(date -u +%FT%TZ)"
df -B1 /project/community | tail -1
timeout 60 du -s -B1M $X/o/174101 $X/o/174101_live $X/o/174101_gate $X/o/174101_gate_f 2>&1 | head
ls -la --time-style=+%H:%M $X/o/174101_live | tail -n +2 | head -20
cat $X/o/174101_live/gate.txt 2>/dev/null | head -5
TZ=UTC squeue -u jjyeung -h -o '%i|%j|%P|%T|%M' | head

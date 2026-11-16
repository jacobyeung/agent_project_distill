N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N && date -u +%FT%TZ; cat evidence/B7C_START.txt evidence/B7C_END.txt 2>/dev/null; for f in evidence/B7_NSDEPTH_MAPPED.rc evidence/B7C_OUTER.rc evidence/B7C_COLLECT.rc; do echo "$f $(cat $f 2>/dev/null)"; done
echo "=== NSDEPTH mapped (inside namespace)"; cat evidence/B7_NSDEPTH_MAPPED.log | head -40
tmux ls 2>&1 | grep k1b7

N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N && date -u +%FT%TZ && ls evidence/ | grep B7_ ; for f in evidence/B7_*.rc; do echo "$f $(cat $f)"; done; tail -c 1500 evidence/B7_MAPPED.log 2>/dev/null; tmux ls 2>&1 | grep k1b7

K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
date -u +%T; tail -4 runner.log; cat meter/METER.json; echo; tmux ls | cut -c1-60
pgrep -af 'kit/nvrun.py' | cut -c1-120
tail -3 meter/CALLS.jsonl | /scratch/jjyeung/envs/p1cpu/bin/python -c "
import sys, json
for l in sys.stdin: r = json.loads(l); print(r['utc'], r['job'], r['model'].split('/')[-1], r['status'], r.get('secs'))"
du -sh out analysis_only scores meter v6 v6b v2 kit faults c1 v1 2>/dev/null | tr '\n' ' '; echo; ls -la out/ | tail -n +2 | awk '{s+=$5} END {print "out bytes", s}'

timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
K=/scratch/jjyeung/orch_n30/sb_ktfix2; date -u +%TZ; head -8 $K/out/tower_frames/run_A.log | cut -c1-200; grep -c DONE $K/out/tower_frames/run_A.log
python3 -c "
import json;c=json.load(open('$K/configs/kit.json'));print({k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in c.items()})" 2>&1 | cut -c1-800
grep -n -E "captures|units|HALTED|resume" $K/code/runner.py | head -12 | cut -c1-200
Y

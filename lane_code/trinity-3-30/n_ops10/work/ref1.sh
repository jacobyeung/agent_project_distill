J=174113; X=/project/community/jjyeung/okh7/x_22c714e1; echo "REF1 $(date -u +%FT%TZ)"
TZ=UTC sacct -j $J -X -n -o JobID,State,ExitCode,Elapsed,End 2>&1 | head -2
ls -la --time-style=+%H:%M:%S $X/o/$J | tail -n +4 | head -30
timeout 120 srun --overlap --jobid=$J -N1 -n1 --mem=1G bash -c '
N=/tmp/q_22c714e1_174113; cd $N 2>/dev/null || exit 0; ls -la --time-style=+%H:%M:%S p/q | head -40
python3 - <<PY
import json,glob
for f in sorted(glob.glob("p/q/*.json"))[:40]:
    try: d=json.load(open(f))
    except Exception as e: print(f,"unreadable",e); continue
    if isinstance(d,dict):
        for k in ("status","refusal","reason","reasons","error","stage","code"):
            if k in d: print(f,k,"=",str(d[k])[:700])
PY' < /dev/null 2>&1 | cut -c1-800

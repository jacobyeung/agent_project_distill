export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7; R=$KB/runs/359fcc3c
date -u +%FT%TZ; squeue -u jjyeung -h -o '%i %j %P %T %M %N' 2>&1
echo "== steps"; tail -3 $KB/o/170111.steps; tail -2 $KB/o/170111.w.steps
echo "== done"; ls -la --time-style=+%FT%T $KB/o/ | grep 'gcs_359fcc3c_m.*\.done' | tail -4
echo "== err"; tail -c 4000 $KB/o/170111.err | tr -c '[:print:]\n' ' ' | grep -v -i 'FutureWarning\|set_state_dict_type\|^ *$' | tail -4
echo "== metrics"; ls -la --time-style=+%FT%T $R/metrics_170111.jsonl
tail -c 1500000 $R/metrics_170111.jsonl | /usr/bin/python3 -I -c '
import sys, json, math
rows=[]
for l in sys.stdin.read().split("\n")[1:-1]:
    try: rows.append(json.loads(l))
    except ValueError: pass
for r in rows[-4:]:
    k=r["ranks"]; m={s: sum(x["stream_means"][s] for x in k)/len(k) for s in ("pose","vqa","routing","pointing")}
    print(r["step"], len(k), round(k[0]["wall_seconds"],1), " ".join("%s=%.4f"%(s,v) for s,v in m.items()), "nonfinite" if not all(math.isfinite(v) for v in m.values()) else "")
'
echo "== free"; df -h /project/community/jjyeung/okh7/r/63e57182 2>&1 | tail -1

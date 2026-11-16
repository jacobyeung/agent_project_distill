<!-- recovered by seal_plan: transcript=71f94277 line=31750 utc=2026-11-14T14:20:21.267Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json
D='/scratch/jjyeung/orch_cd/evalx/work/milestone/native_probe_s23_01/pilot3_failure'
r=json.load(open(D+'/FAILURE_REPORT.json'))
print(json.dumps(r['p1_mismatches'])[:1200]); print(r['p1_checked'],r['p1_argmax_exact'],r['probe_generated_tokens'],json.dumps(r['probe_calls'])[:400])
g=json.load(open(D+'/GPU_PARITY.json'))
print({k:(v if not isinstance(v,(dict,list)) else '...') for k,v in g.items()})
p1=g['P1']; print({k:(v if not isinstance(v,(dict,list)) else '...') for k,v in p1.items()}); print(json.dumps(p1.get('sequence'))[:400])
t=json.load(open(D+'/PROBE_TOKEN_TOP2_TRACE.json'))
rows=t if isinstance(t,list) else t.get('positions') or t.get('trace') or t
print(type(rows), (list(rows.keys())[:10] if isinstance(rows,dict) else len(rows)))
if isinstance(rows,list):
    print(json.dumps(rows[0])[:400])
    ms=sorted([(x.get('margin'),i) for i,x in enumerate(rows) if isinstance(x,dict) and x.get('margin') is not None])[:12]
    print('smallest margins',ms)
    import collections
    print('margin quantum check', collections.Counter(round((x.get('margin') or 0)%0.125,4) for x in rows if isinstance(x,dict)).most_common(5))
    mx=[max(x.get('logits') or [0]) for x in rows if isinstance(x,dict)]
    print('top logit range',min(mx),max(mx))
EOF
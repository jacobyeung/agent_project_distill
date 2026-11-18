<!-- recovered by seal_plan: transcript=71f94277 line=23177 utc=2026-11-13T17:58:27.573Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
m = j["metrics"]["metrics_169097.jsonl"]
print({k: (v if not isinstance(v, str) else v[:80]) for k, v in m.items() if k not in ("first_line", "last_line", "tail")})
for key in ("first_line", "last_line"):
    if key in m:
        try:
            d = json.loads(m[key])
        except Exception as e:
            print(key, "unparsed", m[key][:300]); continue
        r0 = d["ranks"][0]
        print(key, "step", d["step"], "wall", round(r0.get("wall_seconds", 0), 1), "data", round(r0.get("data_seconds", 0), 1))
        print("   keys:", [k for k in r0.keys()][:40])
        for k in ("stream_means", "loss", "losses", "lr", "learning_rate", "grad_norm", "peak_memory_bytes", "peak_gib"):
            if k in r0: print("   ", k, json.dumps(r0[k])[:500])
EOF
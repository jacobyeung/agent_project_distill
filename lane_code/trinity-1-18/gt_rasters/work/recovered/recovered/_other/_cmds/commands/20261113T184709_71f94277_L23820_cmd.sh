<!-- recovered by seal_plan: transcript=71f94277 line=23820 utc=2026-11-13T18:47:09.439Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/orchard_cp2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/logs/production_last.json <<'EOF'
import json, sys, re
j = json.load(open(sys.argv[1]))
t = j["logs"]["169097.out"]["tail"]
print("tail chars", len(t), "of bytes", j["logs"]["169097.out"]["bytes"])
lines = t.split("\n")
kept = []
for l in lines:
    if "FutureWarning" in l or "FullyShardedDataParallel" in l or "set_state_dict_type" in l or not l.strip():
        continue
    kept.append(l[:220])
print(len(lines), "lines in tail;", len(kept), "non-warning lines:")
for l in kept[-25:]:
    print("  ", l)
EOF
ls $C/out/step1_169097 2>/dev/null | head -n 20
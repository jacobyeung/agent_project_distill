<!-- recovered by seal_plan: transcript=71f94277 line=28954 utc=2026-11-14T06:06:17.361Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/if_p0/inbox_results/a35f2d78fe7c5ee8d; ls $D $D/returned 2>/dev/null | head -n 30; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$D/returned" <<'EOF'
import json, sys, os, glob
r = sys.argv[1]
for name in glob.glob(r + "/**/*.json", recursive=True):
    v = json.load(open(name))
    print("==", os.path.relpath(name, r))
    if "FAILED" in name:
        print(json.dumps(v)[:800])
    elif "JOB_EVIDENCE" in name:
        ph = v.get("phases", {})
        for k, p in ph.items():
            print("  phase", k, {kk: (str(vv)[:90]) for kk, vv in p.items() if kk in ("elapsed_seconds", "seconds", "bytes", "path", "interpreter_relative", "exercised", "passed")})
        print("  storage:", str(v.get("storage"))[:300])
        print("  allocation:", v.get("allocation"))
        print("  commands:", len(v.get("commands", [])))
    else:
        print(json.dumps(v)[:400])
EOF
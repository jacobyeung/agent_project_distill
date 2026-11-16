<!-- recovered by seal_plan: transcript=71f94277 line=25365 utc=2026-11-13T21:23:16.302Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/leg_s1_canary; sha256sum $C/out/state_copy_169097_20261113T2114Z_96cf964f.tgz $C/out/STATE_COPY_OPERATOR_169097_20261113T2114Z_96cf964f.json $C/out/STATE_COPY_TRANSPORT_DIFF_20261113T2118Z_6bc9c7f8.patch | cut -c1-16,65- | sed "s#$C/out/##"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/out/STATE_COPY_FIXTURES_20261113T2113Z_38ef1cbc.json <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
def find(o, depth=0):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("passed", "failed", "count", "total", "status", "result", "returncode", "command", "cwd", "address_space_bytes"):
                print("  " * depth + f"{k}: {str(v)[:200]}")
            elif isinstance(v, (dict,)) and depth < 2:
                find(v, depth + 1)
find(j)
print(list(j.keys())[:20])
EOF
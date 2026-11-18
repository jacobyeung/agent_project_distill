<!-- recovered by seal_plan: transcript=71f94277 line=25179 utc=2026-11-13T21:06:40.242Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/evalx/work/milestone; grep -n "ARCHIVE_LIMIT *=\|ALLOWANCE *=\|class LimitedWriter" $C/chain_save.py | head -n 5; ls $C | grep -E "^test_orchard" ; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/ORCHARD_LAUNCHER_CONFIRMATION_REQUEST.json <<'EOF'
import json, sys, hashlib
j = json.load(open(sys.argv[1]))
pins = j["code_pins"]
ok = all(hashlib.sha256(open(p, "rb").read()).hexdigest() == h for p, h in pins.items())
print("pins", len(pins), "match", ok, "| digest field", j["code_pins_sha256"][:16], "| recomputed", hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()[:16])
print("packet sha", hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()[:16])
EOF
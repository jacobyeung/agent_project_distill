<!-- recovered by seal_plan: transcript=71f94277 line=25555 utc=2026-11-13T21:48:57.895Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd/evalx/work/milestone; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $C/ORCHARD_MOUNT_CONFIRMATION_REQUEST.json <<'EOF'
import json, sys, hashlib
j = json.load(open(sys.argv[1]))
pins = j["code_pins"]
ok = all(hashlib.sha256(open(p, "rb").read()).hexdigest() == h for p, h in pins.items())
print("pins", len(pins), "match", ok, "| digest", j["code_pins_sha256"][:16], "| recomputed", hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()[:16], "| packet", hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()[:16])
EOF
cd /scratch/jjyeung/orch_home_distill && timeout 300 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -m pytest -q -p no:cacheprovider $C/test_orchard_mount.py $C/test_orchard_launcher.py $C/test_orchard_results.py $C/test_orchard_review_findings.py 2>&1 | tail -n 2
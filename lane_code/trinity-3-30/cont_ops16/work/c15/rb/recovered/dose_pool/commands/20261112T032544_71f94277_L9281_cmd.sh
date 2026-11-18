<!-- recovered by seal_plan: transcript=71f94277 line=9281 utc=2026-11-12T03:25:44.363Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; grep -n -i -E "fps|hz|frame_rate" dose_pool/work/dosepool/resolve9b.py dose_pool/work/dosepool/export9b.py dose_pool/work/dosepool/frames.py 2>/dev/null | cut -c1-260 | head -24; python3 - <<'EOF'
import json
d=json.load(open('/scratch/jjyeung/orch_cd/leg_s1_tree/out/FPS_AUTHORITY.json'))
print(json.dumps(d)[:1400])
EOF
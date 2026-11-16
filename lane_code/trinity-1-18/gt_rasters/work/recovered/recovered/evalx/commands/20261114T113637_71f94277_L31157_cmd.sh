<!-- recovered by seal_plan: transcript=71f94277 line=31157 utc=2026-11-14T11:36:37.454Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step400_e3da9a577; ls $D | head -n 40; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,os
D='/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step400_e3da9a577'
for name in ('DECISION.json','PACKET_READY.json'):
    p=os.path.join(D,name)
    if not os.path.exists(p): print('missing',name); continue
    d=json.load(open(p))
    print(name, list(d.keys())[:40])
EOF
<!-- recovered by seal_plan: transcript=71f94277 line=9285 utc=2026-11-12T03:25:53.765Z kind=commands original_path=(bash command)  -->
python3 - <<'EOF'
import json,collections
d=json.load(open('/scratch/jjyeung/orch_cd/leg_s1_tree/out/FPS_AUTHORITY.json'))
print([k for k in d.keys()])
c=collections.defaultdict(collections.Counter)
for k,v in d.get('by_scene',{}).items(): c[k.split('/')[0]][v]+=1
for g in c: print(g, dict(c[g]))
for k in d:
    if k!='by_scene': print(k, json.dumps(d[k])[:500])
EOF
sed -n 66,84p /scratch/jjyeung/orch_cd/dose_pool/work/dosepool/export9b.py | cut -c1-200
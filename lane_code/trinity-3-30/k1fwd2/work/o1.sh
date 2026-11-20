D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5; cd $D || exit 1
ls -la | head -50
/usr/bin/python3 - <<'PY'
import json
c=json.load(open('944b6b6a8f8d8c7f.a.json'))
print('KEYS',sorted(c))
for k in sorted(c):
    if k!='code': 
        v=json.dumps(c[k]); print(k, v[:300])
m=c['code']['members']; print('NMEMBERS',len(m)); print('CODEKEYS',[k for k in c['code'] if k!='members'], {k:c['code'][k] for k in c['code'] if k!='members'})
import re
for n in sorted(m):
    if re.search(r'student_pilot/(decoupled_v|decoupled_vc|point_depth_head|carrier_c1|carrier_c1_decode|p3_heads|tower_read|_tower_native|fixed_readout|carrier_c1_data|ground_context)\.py$',n) or n.endswith('k1_phases.py') or n.endswith('boundaries.py'):
        print('M',n,m[n])
PY
TZ=UTC squeue -p advanced -o '%i %j %u %T %M %l %N %b %R' | head -30
TZ=UTC date

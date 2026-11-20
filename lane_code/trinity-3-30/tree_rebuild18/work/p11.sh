W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; P=$W/w24/work/build24m4/hidden/payload/947cbb9fa7d6bde05b034a0b78bfa8ead473e545ab02ac3bd698486fd30425ab; sha256sum $P | cut -c1-16; ls -l $P
nice -n 10 python3 - <<'PY'
import json
m=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m4/hidden/inputs/0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a'))
print(json.dumps(m.get('direct_rule_audit'))[:3000]); print('blockers',m.get('blockers'),'status',m.get('status'),'native_rows',m.get('native_rows'))
print(json.dumps(m.get('contract_identity', {k:m.get(k) for k in m if 'contract' in k}))[:800])
print(sorted(m.keys()))
PY

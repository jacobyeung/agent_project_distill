set -u
cd /scratch/jjyeung/orch_n30 || exit 1
echo "== host $(hostname -s)"; df -h /scratch | tail -1
for d in rows_rebuild rows_rebuild/s0 rows_rebuild/s0/pull rows_rebuild/s0/pull/m3; do echo "== ls $d"; ls $d 2>&1 | head -20; done
F=rows_rebuild/s0/pull/m3/frame_plan.json.gz; ls -la $F 2>&1
timeout 120 python3 - <<'PY'
import gzip, json, collections
F='rows_rebuild/s0/pull/m3/frame_plan.json.gz'
try:
    d=json.load(gzip.open(F))
except Exception as e:
    print('ERR', e); raise SystemExit
print('type', type(d).__name__, 'len', len(d))
if isinstance(d, dict):
    ks=list(d)[:8]; print('keys', ks)
    for k in ks[:3]:
        print(k, str(d[k])[:700])
else:
    for x in d[:2]: print(str(x)[:700])
PY
H=rows_a2/vsti/out/vsti_rel_v4/HELD_LR_ROTATED.json; ls -la $H
timeout 60 python3 -c "
import json; d=json.load(open('$H')); print(type(d).__name__, len(d)); print(str(d)[:900])"
echo "== trin_read root"; ls trin_read/root 2>&1 | head; ls trin_read/root/k6tk/parts 2>&1 | head

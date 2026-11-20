/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY' 1>&2
import json
d = json.load(open('/scratch/jjyeung/orch_n30/fb_pack/k1point/AUDIT_POINTING_K1.json'))
print(type(d).__name__, list(d)[:20] if isinstance(d, dict) else len(d))
for k in (list(d)[:20] if isinstance(d, dict) else []): print(k, json.dumps(d[k])[:300])
PY
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import sqlite3, json, gzip, sys
c = sqlite3.connect('file:/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite?mode=ro', uri=True)
out = gzip.GzipFile(fileobj=sys.stdout.buffer, mode='wb')
for i, row, target in c.execute('select i, row, target from rows'):
    r = json.loads(row); p = r.get('pointing') or {}; pv = r.get('provenance') or {}
    out.write((json.dumps({'i': i, 'qid': r.get('qid'), 'd': r.get('dataset'), 'scene': pv.get('canonical_scene'), 'store': pv.get('frame_store'), 'frame': p.get('frame'), 'rgb': p.get('rgb_sha256'),
        'label': p.get('label'), 'kind': p.get('kind'), 'stratum': p.get('stratum'), 'area': p.get('area_fraction'), 'uv': (p.get('selected') or {}).get('uv'), 'yx': (p.get('selected') or {}).get('pixel_yx'),
        'shape': (p.get('selected') or {}).get('shape'), 'target': target[:300]}) + '\n').encode())
out.close()
PY

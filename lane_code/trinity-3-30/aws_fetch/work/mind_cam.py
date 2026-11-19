import gzip, hashlib, json, os, sqlite3, time
E = '/lab_data/tarrlab/jacoby/agent_project/aws_evac/d/w19/evid'
SRC = E + '/8865619b_469ddece_inputs/routing_rows.sqlite'
PIN = 'c48d5b6201c935e2de8e985d2d8a163d9bb46603e693e790733e3c86fe59db53'
TYPES = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
OUT = E + '/camera_rows'
os.makedirs(OUT, exist_ok=True)
h = hashlib.sha256()
with open(SRC, 'rb') as f:
    for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
src_sha = h.hexdigest()
con = sqlite3.connect('file:%s?mode=ro&immutable=1' % SRC, uri=True)
cnt = {t: 0 for t in TYPES}; other = {}; total = 0
dst = OUT + '/routing_camera_rows.jsonl.gz'
with gzip.open(dst + '.part', 'wt') as o:
    for i, row, target in con.execute('SELECT i, row, target FROM rows ORDER BY i'):
        total += 1
        rj = json.loads(row)
        qt = (rj.get('routing') or {}).get('question_type') if isinstance(rj.get('routing'), dict) else None
        qt = qt or rj.get('question_type')
        if qt in cnt:
            cnt[qt] += 1
            o.write(json.dumps({'i': i, 'row': row, 'target': target}) + '\n')
        else:
            other[str(qt)] = other.get(str(qt), 0) + 1
os.rename(dst + '.part', dst)
oh = hashlib.sha256(open(dst, 'rb').read()).hexdigest()
man = {'schema': 'camera-rows-extract-v1', 'source': {'path': SRC, 'pinned_path': 'ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/routing/rows.sqlite',
       'sha256': src_sha, 'pin_ok': src_sha == PIN, 'rows': total},
       'selection': 'rows whose row.routing.question_type (else row.question_type) is one of ' + ','.join(TYPES),
       'columns': 'i, row (raw TEXT), target (raw TEXT)', 'counts': cnt, 'receipt_counts': {'camera_displacement': 14020, 'camera_rotation': 9143, 'camera_movement_direction': 12260},
       'other_types': other, 'out': {'path': dst, 'bytes': os.path.getsize(dst), 'sha256': oh},
       'host': os.uname()[1], 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
json.dump(man, open(OUT + '/MANIFEST.json', 'w'), indent=1, sort_keys=True)
print('MANIFEST ' + json.dumps(man, sort_keys=True), flush=True)

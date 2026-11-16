import hashlib, json, os, sys
m = json.load(open(sys.argv[1])); root = sys.argv[2]; bad = 0
for f in m['files']:
    p = os.path.join(root, f['path'])
    if not os.path.exists(p):
        bad += 1; print('BAD missing', f['path']); continue
    data = open(p, 'rb').read()
    ok = hashlib.sha256(data).hexdigest() == f['sha256'] if f.get('sha256') else hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest() == f['blob']
    if not ok:
        bad += 1; print('BAD hash', f['path'])
print('manifest files', len(m['files']), 'bad', bad); sys.exit(1 if bad else 0)

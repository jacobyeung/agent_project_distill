import hashlib, json, os, sys
n, o = sys.argv[1], sys.argv[2]
out = []
for d, ds, fs in os.walk(n):
    if not d.replace(os.sep, '/').endswith('/p/q/selection'):
        continue
    for f in sorted(fs):
        p = os.path.join(d, f)
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        with open(p, 'rb') as h:
            head = h.read(100)
            if not (f.endswith('.sqlite') or head.startswith(b'SQLite format 3\x00')):
                continue
            whole = hashlib.sha256(head); body = hashlib.sha256()
            for b in iter(lambda: h.read(1 << 22), b''):
                whole.update(b); body.update(b)
        out.append(dict(path=os.path.relpath(p, n), size=os.path.getsize(p), sha256=whole.hexdigest(),
                        head100_hex=head.hex(), body_sha256=body.hexdigest()))
if not out:
    sys.exit(1)
t = os.path.join(o, '.db_bytes.json.tmp')
with open(t, 'w') as h:
    json.dump(dict(files=out), h, indent=1)
os.replace(t, os.path.join(o, 'db_bytes.json'))
print('db_bytes', json.dumps([(x['path'], x['size'], x['sha256'][:16], x['body_sha256'][:16]) for x in out]))

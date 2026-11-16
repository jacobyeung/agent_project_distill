"""Verify a staged tree: every listed file present, size equal to the reader's size log (and to LIST_*.json sizes and
sha256 when given); no extra files. usage: verify_stage.py LIST DEST SIZES [LIST_JSON]"""
import hashlib, json, os, sys
lst, dest, sizes = sys.argv[1:4]
names = [l.strip() for l in open(lst) if l.strip()]
log = dict(l.rstrip('\n').split('\t') for l in open(sizes))
pin = {r['path']: r for r in json.load(open(sys.argv[4]))} if len(sys.argv) > 4 else {}
bad = []
for n in names:
    p = os.path.join(dest, n)
    if not os.path.isfile(p): bad.append((n, 'missing')); continue
    s = os.path.getsize(p)
    if str(s) != log.get(n): bad.append((n, 'size %d vs reader %s' % (s, log.get(n))))
    if n in pin:
        if s != pin[n]['size']: bad.append((n, 'size %d vs list %d' % (s, pin[n]['size'])))
        if hashlib.sha256(open(p, 'rb').read()).hexdigest() != pin[n]['sha256']: bad.append((n, 'sha256'))
on_disk = sum(len(f) for _, _, f in os.walk(dest))
print(json.dumps(dict(listed=len(names), logged=len(log), on_disk=on_disk, bytes=sum(int(v) for v in log.values()),
                      sha_checked=len(pin), bad=bad[:20], n_bad=len(bad))))
sys.exit(1 if bad or on_disk != len(names) else 0)

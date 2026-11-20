import hashlib, json, os, sys
from multiprocessing import Pool
TARGET = os.environ.get('DBB_TARGET', '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84')
n, o = sys.argv[1], sys.argv[2]
u = sys.argv[3] if len(sys.argv) > 3 else None


def files():
    out = []
    for d, ds, fs in os.walk(n):
        if not d.replace(os.sep, '/').endswith(('/p/q/selection', '/p/q/base')):
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
    return out


def write(v):
    t = os.path.join(o, '.db_bytes.json.tmp')
    with open(t, 'w') as h:
        json.dump(v, h, indent=1)
    os.replace(t, os.path.join(o, 'db_bytes.json'))


def trial(args):
    p, head, ver = args
    h = bytearray(head); h[96:100] = ver.to_bytes(4, 'big')
    s = hashlib.sha256(bytes(h))
    with open(p, 'rb') as f:
        f.seek(100)
        for b in iter(lambda: f.read(1 << 22), b''):
            s.update(b)
    return ver if s.hexdigest() == TARGET else None


out = files()
if not out:
    sys.exit(1)
v = dict(target_sha256=TARGET, files=out)
if u:
    import shutil
    for x in out:
        if x['sha256'] == TARGET or not x['path'].replace(os.sep, '/').endswith(('/p/q/selection/rows.sqlite',)) or x['size'] >= 1_000_000_000:
            x['pool_copy'] = None
            continue
        dst = os.path.join(u, x['sha256'])
        if not os.path.exists(dst):
            tmp = os.path.join(u, '.%s.tmp' % x['sha256'])
            shutil.copyfile(os.path.join(n, x['path']), tmp)
            with open(tmp, 'rb') as h:
                s2 = hashlib.sha256()
                for b in iter(lambda: h.read(1 << 22), b''):
                    s2.update(b)
            if s2.hexdigest() != x['sha256']:
                raise SystemExit('copy hash differs ' + x['path'])
            os.chmod(tmp, 0o400); os.replace(tmp, dst)
        x['pool_copy'] = 'u/' + x['sha256']
write(v)
print('db_bytes', json.dumps([(x['path'], x['size'], x['sha256'][:16], x['body_sha256'][:16]) for x in out]), flush=True)
for x in out:
    head = bytes.fromhex(x['head100_hex'])
    x['equal_target'] = x['sha256'] == TARGET
    own = int.from_bytes(head[96:100], 'big')
    x['header_96_99_version'] = own
    if x['equal_target']:
        write(v)
        continue
    vers = [w for w in (3000000 + mi * 1000 + pa for mi in range(7, 61) for pa in range(0, 21)) if w != own]
    p = os.path.join(n, x['path'])
    with Pool(8) as pool:
        hits = [r for r in pool.imap_unordered(trial, [(p, head, w) for w in vers], chunksize=4) if r is not None]
    x['header_search'] = dict(bytes='96-99 (SQLITE_VERSION_NUMBER), all other bytes unchanged', candidates=len(vers),
                              range='3.7.0..3.60.20', found=[dict(version=w, hex=w.to_bytes(4, 'big').hex()) for w in hits])
    write(v)
    print('header_search', x['path'], 'found', hits, flush=True)

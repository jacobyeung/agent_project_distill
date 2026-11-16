python3 - <<'PY'
import base64, hashlib, os, sys
F = '/project/community/jjyeung/cp4tk_fr/k6tk/parts'
want = {'0a026c4437f78beb4cc8e7255c6fd3086a3c39a0c99820300c735f9fa4861b6e': 'v1n3/v1n3_000.tar',
        '12a54e2cf5f298e9c950f6f463ba97213a9fff8d0d211f04cb3ca079e30de503': 'v0n3/v0n3_000.tar',
        '14fbb934a25b7f3f79fdefc0752309636a0c7cb9fe051f8fb266700f7d052844': 'v1n3/v1n3_000.tar',
        'abc0368114826f8f83e105db66f99606c91a3e82d48391dfd99e166b0a222df5': 'v2n3/v2n3_001.tar'}
for sha, shard in sorted(want.items(), key=lambda x: x[1]):
    name = sha[:2] + '/' + sha + '.png'
    with open(os.path.join(F, shard), 'rb') as f:
        off = 0; found = None; n = 0
        while True:
            f.seek(off); h = f.read(512); n += 1
            if len(h) < 512 or h == b'\0' * 512: break
            mname = h[0:100].split(b'\0')[0].decode(); prefix = h[345:500].split(b'\0')[0].decode()
            full = (prefix + '/' + mname) if prefix else mname
            size = int(h[124:136].split(b'\0')[0].strip() or b'0', 8)
            if full == name:
                f.seek(off + 512); found = f.read(size); break
            off += 512 + (size + 511) // 512 * 512
    if found is None:
        print('NOTFOUND', sha, shard, n); continue
    print('FILE', sha, len(found), hashlib.sha256(found).hexdigest(), n)
    print(base64.b64encode(found).decode()); sys.stdout.flush()
PY

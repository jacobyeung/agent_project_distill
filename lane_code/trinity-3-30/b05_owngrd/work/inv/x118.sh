X=/scratch/jjyeung/orch_n30/b05_owngrd_x118; mkdir -p $X/sub; cat > $X/st_extract.py <<'PYEOF'
"""Stream a tar of safetensors shards from stdin; keep only tensors whose names match the given prefixes/substrings.
Writes <out>/subset.safetensors plus <out>/subset.json (names, shapes, dtypes, source shard, sha256 of each tensor's bytes)
and copies small non-safetensors members (json/txt) verbatim. Usage: cat parts* | python3 st_extract.py OUT pat1 pat2 ..."""
import hashlib, json, os, struct, sys, tarfile
out, pats = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
keep, meta = {}, {}
tf = tarfile.open(fileobj=sys.stdin.buffer, mode='r|')
for m in tf:
    if not m.isfile():
        continue
    f = tf.extractfile(m)
    base = os.path.basename(m.name)
    if not base.endswith('.safetensors'):
        if m.size < 50_000_000:
            data = f.read(); open(os.path.join(out, base), 'wb').write(data)
        continue
    n = struct.unpack('<Q', f.read(8))[0]
    header = json.loads(f.read(n))
    items = sorted(((k, v) for k, v in header.items() if k != '__metadata__'), key=lambda kv: kv[1]['data_offsets'][0])
    pos = 0
    for k, v in items:
        a, b = v['data_offsets']
        if a > pos:
            f.read(a - pos); pos = a
        want = any(p in k for p in pats)
        if want:
            data = f.read(b - a)
            keep[k] = (v['dtype'], v['shape'], data)
            meta[k] = dict(dtype=v['dtype'], shape=v['shape'], shard=base, sha256=hashlib.sha256(data).hexdigest())
        else:
            left = b - a
            while left:
                chunk = f.read(min(left, 64 << 20)); left -= len(chunk)
        pos = b
    print(base, 'kept', sum(1 for x in meta.values() if x['shard'] == base), flush=True)
hdr, off = {}, 0
for k in sorted(keep):
    dt, sh, data = keep[k]
    hdr[k] = dict(dtype=dt, shape=sh, data_offsets=[off, off + len(data)]); off += len(data)
hb = json.dumps(hdr, separators=(',', ':')).encode(); hb += b' ' * ((8 - len(hb) % 8) % 8)
with open(os.path.join(out, 'subset.safetensors'), 'wb') as w:
    w.write(struct.pack('<Q', len(hb))); w.write(hb)
    for k in sorted(keep):
        w.write(keep[k][2])
json.dump(meta, open(os.path.join(out, 'subset.json'), 'w'), indent=1, sort_keys=True)
print('tensors', len(keep), 'bytes', off)
PYEOF
cat > $X/run.sh <<'SHEOF'
set -u
X=/scratch/jjyeung/orch_n30/b05_owngrd_x118
cd /scratch/jjyeung
date -u +%FT%TZ > $X/START
cat k1/m544_parts/469ddece_mstop.tar.part0{0,1,2,3}-of-04 | nice -n 10 python3 $X/st_extract.py $X/sub visual embed_tokens > $X/extract.log 2>&1
echo rc=$? >> $X/extract.log
sha256sum $X/sub/* > $X/sub/SHA256SUMS
tar cf - -C $X sub | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b05_owngrd/work/m544sub && cd /scratch/jjyeung/orch_n30/b05_owngrd/work/m544sub && tar xf -"
tar cf - -C /scratch/jjyeung/orch_cd/mdg_build/work t0bundle/base weights/resnet18-f37072fd.pth -C /scratch/jjyeung/orch_cd/own_probe/out own_probe_delivery_r3.tar.gz g3t_taps.py room_gate.py API.md P0_CARD.md | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b05_owngrd/work/from118 && cd /scratch/jjyeung/orch_n30/b05_owngrd/work/from118 && tar xf -"
echo sent rc=$? >> $X/extract.log
date -u +%FT%TZ > $X/END
SHEOF
nohup bash $X/run.sh > $X/run.out 2>&1 &
echo launched; df -h /scratch | tail -1

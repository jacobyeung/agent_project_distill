"""Pixel parity of re-produced student frames against the k6 pins (run on Orchard after every part is DONE).

usage: dparity.py PACKET_ROOT OUT.jsonl
Rule (fixed 2026-11-16 before the full run, from one login-node capture where 29 of 32 byte pins differed by
CPU SIMD dispatch only): a re-produced frame matches its pin when both decode to the same shape and
max |a-b| <= 1 per channel and the fraction of differing values <= 1e-3. Byte-equal frames pass at once.
Inputs: parts/*/out.jsonl and parts/*/*.tar (new frames), the k6 map (sha256 pinned below) and
k6tk/MEMBERS.tsv.gz + k6tk/parts/*/*.tar (pinned frames). Output: one line per compared (scene, ordinal)."""
import glob, gzip, hashlib, json, os, sys, tarfile
import cv2, numpy as np
MAP = os.path.expanduser('~/okit/x/07ca49df/k/frame_map.jsonl.gz')
MAP_SHA = '17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3'
K6 = '/project/community/jjyeung/cp4tk_fr/k6tk'
MAX_ABS, MAX_FRAC = 1, 1e-3


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(16 << 20), b''):
            h.update(b)
    return h.hexdigest()


def compare(a, b):
    if a is None or b is None or a.shape != b.shape:
        return dict(max=None, frac=None, ok=False)
    d = np.abs(a.astype(np.int16) - b.astype(np.int16))
    mx, fr = int(d.max()), float((d > 0).mean())
    return dict(max=mx, frac=round(fr, 7), ok=mx <= MAX_ABS and fr <= MAX_FRAC)


def read_members(tars, names):
    out = {}
    for tp in tars:
        with tarfile.open(tp, 'r:') as t:
            for m in t:
                if m.name in names:
                    out[m.name] = cv2.imdecode(np.frombuffer(t.extractfile(m).read(), np.uint8), cv2.IMREAD_UNCHANGED)
    return out


def main():
    root, out_p = sys.argv[1:3]
    if sha_file(MAP) != MAP_SHA:
        raise SystemExit('k6 map differs from the pinned sha256')
    tasks_v = json.load(gzip.open(root + '/plan/tasks_v.json.gz', 'rt'))
    want = {(s, k) for s, ks in tasks_v['parity'].items() for k in ks}
    got = {}
    for p in glob.glob(root + '/parts/*/out.jsonl'):
        for line in open(p):
            r = json.loads(line)
            if 'error' in r:
                continue
            for k in r.get('parity', []):
                want.add((r['s'], k))
            for f in r['frames']:
                got[(r['s'], f[0])] = f[1]
    pins = {}
    with gzip.open(MAP, 'rt') as fh:
        for line in fh:
            r = json.loads(line)
            if (r['s'], r['i']) in want:
                pins[(r['s'], r['i'])] = r['sha256']
    pairs = {sk: (pins[sk], got[sk]) for sk in want if sk in pins and sk in got}
    differ = {sk: v for sk, v in pairs.items() if v[0] != v[1]}
    old_names = {o[:2] + '/' + o + '.png' for o, _ in differ.values()}
    new_names = {n[:2] + '/' + n + '.png' for _, n in differ.values()}
    where = {}
    with gzip.open(K6 + '/MEMBERS.tsv.gz', 'rt') as fh:
        for line in fh:
            sha, tar = line.rstrip('\n').split('\t')[:2]
            if sha[:2] + '/' + sha + '.png' in old_names:
                where.setdefault(tar, set()).add(sha[:2] + '/' + sha + '.png')
    old = read_members([glob.glob(f'{K6}/parts/*/{t}')[0] for t in where], old_names)
    new = read_members(sorted(glob.glob(root + '/parts/*/*.tar')), new_names)
    n_ok = n_bad = 0
    with open(out_p, 'w') as fo:
        for (s, k), (o, n) in sorted(pairs.items()):
            if o == n:
                rec = dict(s=s, k=k, byte_equal=True, ok=True)
            else:
                rec = dict(s=s, k=k, byte_equal=False, pinned=o, fetched=n,
                           **compare(old.get(o[:2] + '/' + o + '.png'), new.get(n[:2] + '/' + n + '.png')))
            n_ok += rec['ok']; n_bad += not rec['ok']
            fo.write(json.dumps(rec) + '\n')
    print(json.dumps(dict(wanted=len(want), compared=len(pairs), byte_equal=len(pairs) - len(differ),
                          pixel_ok=n_ok - (len(pairs) - len(differ)), failed=n_bad,
                          missing_pin=len([x for x in want if x not in pins]), missing_fetch=len([x for x in want if x not in got]))))


if __name__ == '__main__':
    main()

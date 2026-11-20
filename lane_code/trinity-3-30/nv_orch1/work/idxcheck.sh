J=/project/community/jjyeung/4f5e45fe5d74c; tail -2 $J/log/173621.out; ls -la $J/idx
python3 - <<'PY'
import gzip, hashlib, random, json
J = '/project/community/jjyeung/4f5e45fe5d74c'
idx = {}
for l in gzip.open(J + '/idx/k6.tsv.gz', 'rt'):
    h, p, o, s = l.rstrip('\n').split('\t'); idx[h] = (p, int(o), int(s))
want = set(gzip.open(J + '/hold/WANT_k6.txt.gz', 'rt').read().split())
q = [json.loads(l) for l in open(J + '/hold/v7/20_v7p.jsonl')]
need = set(c['image'][4:] for t in q for c in t['content'] if 'image' in c)
print('index', len(idx), 'want', len(want), 'missing want', len(want - set(idx)), 'v7 queue frames', len(need), 'missing', len(need - set(idx)))
bad = 0
for h in random.Random(1).sample(sorted(need), 40):
    p, o, s = idx[h]
    with open(p, 'rb') as f: f.seek(o); b = f.read(s)
    bad += hashlib.sha256(b).hexdigest() != h
print('sha check 40 frames, bad', bad)
PY

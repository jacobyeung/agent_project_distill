"""fix21 test of the kit's pc.Copier.metrics on a synthetic run folder: a metrics file of P's size class (~76 MB of
per-step JSON lines), round trip, cap behaviour, and that copy.json's budget is untouched. Usage: tmet.py <kit b dir> <out dir (new)>"""
import gzip, json, random, sys, importlib.util, hashlib
from pathlib import Path
B, D = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); assert not D.exists()
spec = importlib.util.spec_from_file_location('pc', B/'pc.py'); pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)
def copier(name):
    c = object.__new__(pc.Copier); root = D/name
    c.train = root/'p/q/r'; c.live = root/'X/o/1/live'; c.spool = root/'live_spool'
    c.train.mkdir(parents=True); c.spool.mkdir(parents=True); return c
random.seed(0)
line = lambda s: json.dumps(dict(step=s, rank=random.randrange(4), losses={k: random.random() for k in ('pose','vqa','routing','pointing','lm')},
    grad_norm=random.random(), lr=1e-5*random.random(), wall_seconds=133.0+random.random(), heads={f'h{i}': random.random() for i in range(40)})) + '\n'
c = copier('full'); f = c.train/'metrics_174999.jsonl'
with f.open('w') as o:
    n = 0
    while f.stat().st_size < 76_000_000 if f.exists() else True:
        o.write(''.join(line(n) for _ in range(2000))); o.flush(); n += 1
o.close()
with f.open('a') as o: o.write('{"partial": ')   # an unfinished last line
rows = c.metrics(); r = rows[0]
data = (c.live/r['name']).read_bytes(); back = gzip.decompress(data)
src = f.read_bytes()
out = dict(full=dict(source_bytes=r['source_bytes'], gz_bytes=r['bytes'], ratio=round(r['source_bytes']/r['bytes'], 2),
    omitted=r['omitted_head_bytes'], round_trip_whole_lines=back == src[:src.rfind(b'\n')+1], sha_ok=hashlib.sha256(data).hexdigest() == r['sha256'],
    metrics_json=json.loads((c.live/'metrics.json').read_text())['files'][0]['name'], under_cap=r['bytes'] <= pc.METRICS_CAP))
pc.METRICS_CAP = 1_000_000
c2 = copier('capped'); (c2.train/'metrics_1.jsonl').write_bytes(src[:src.rfind(b'\n')+1])
r2 = c2.metrics()[0]; back2 = gzip.decompress((c2.live/r2['name']).read_bytes())
out['capped_1MB'] = dict(gz_bytes=r2['bytes'], under_cap=r2['bytes'] <= 1_000_000, omitted=r2['omitted_head_bytes'], kept=r2['kept_bytes'],
    keeps_newest_whole_lines=src.endswith(back2) if False else (src[:src.rfind(b'\n')+1]).endswith(back2) and back2.startswith(b'{') and all(json.loads(l) for l in back2.splitlines()[:3]))
c3 = copier('none'); out['no_metrics'] = c3.metrics()
print(json.dumps(out, indent=1))

"""Stand-in for the publisher (b/pc.py) of the dying allocation, local only: takes the persistence archive of the
newest state, cuts it into the four byte ranges the writer sends (ceil(size/4) each, as gc.py 'split ... 4 4'),
writes them as files under <durable>, writes the publisher's receipt exactly as pc.py _send puts it
(object, bytes, sha256, marker_sha256, generation) and the resume card b/rs.py reads. Moves no byte off the node.
usage: pub.py <run A folder> <ns> <durable folder> <card out> <source job>"""
import hashlib, json, sys
from pathlib import Path

runA, ns, durable, card_out, job = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), sys.argv[5]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = runA / 'p/q/r'
local = lambda p: runA / Path(p).relative_to(ns)          # a path written inside the view, on the host
receipts = sorted((out / 'persist').glob('*.local.json'))
rows = [json.loads(p.read_text()) for p in receipts]
rows = [r for r in rows if r['kind'] == 'checkpoint']
newest = max(rows, key=lambda r: json.loads(local(r['source']['path']).read_text())['step'])
marker, archive = local(newest['source']['path']), local(newest['archive']['path'])
assert sha(marker) == newest['source']['sha256'] and sha(archive) == newest['archive']['sha256']
raw = archive.read_bytes(); size = len(raw); step = -(-size // 4)
key = 'q9/22c714e1/469ddece_ck00.tar.j' + job
durable.mkdir(parents=True, exist_ok=False)
parts = []
for k in range(4):
    offset = k * step; chunk = raw[offset:offset + step]
    p = durable / f'{Path(key).name}.part{k:02d}-of-04'
    p.write_bytes(chunk)
    parts.append(dict(path=str(p), offset=offset, bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest()))
done = dict(object=key, bytes=size, sha256=newest['archive']['sha256'], marker_sha256=newest['source']['sha256'],
            generation='ck00')
attempt = json.loads((out / f'attempt_{job}.json').read_text())
card = dict(schema='n-resume-card-v1', source_job=job, directory=marker.parent.name, done=done, parts=parts,
            binding=attempt['binding'])
card_out.write_text(json.dumps(card, indent=1, sort_keys=True) + '\n')
print(json.dumps(dict(card=str(card_out), state=marker.parent.name, archive_bytes=size, archive_sha256=done['sha256'],
                      marker_sha256=done['marker_sha256'], parts=[p['bytes'] for p in parts])))

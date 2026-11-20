cd /project/community/jjyeung/cp4tk_fr/k6tk && python3 - <<'PY'
import gzip, json, tarfile, sys, collections, re
plan = json.loads(gzip.decompress(tarfile.open('bin.tar').extractfile('plan/PLAN.json.gz').read()))
a = plan['a']; fr = collections.defaultdict(list)
for l in gzip.open('MAP.jsonl.gz', 'rt'):
    r = json.loads(l)
    if r['d'] == 'd3': fr[r['s']].append((r['i'], r['sha256'], r['w'], r['h']))
out = gzip.GzipFile(fileobj=sys.stdout.buffer, mode='wb')
for v, fs in sorted(fr.items()):
    m = re.search(r'/Training/(\d+)/', a[v]['u']) or re.search(r'/(\w+)/(\d+)/lowres', a[v]['u'])
    vid = m.group(1) if m else None
    fs.sort(); out.write((json.dumps({'v': v, 'video': vid, 'split': 'Training' if '/Training/' in a[v]['u'] else 'other', 'rot': a[v]['rot'], 'total': plan['total'].get(v), 'f': [[i, s] for i, s, w, h in fs], 'wh': sorted(set((w, h) for _, _, w, h in fs))}) + '\n').encode())
out.close()
PY

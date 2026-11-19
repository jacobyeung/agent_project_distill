import sqlite3, json, hashlib, re, sys, time, collections
def tok(ds, scene): return 'v' + hashlib.sha256(('rung1 scene %s/%s' % (ds, scene)).encode()).hexdigest()[:12]
print('test arkit', tok('arkitscenes', '41159526'), 'want vc6a4b809b958 |', 'scannet', tok('scannet', 'scene0060_01'), 'want v006a28d04550')
key = json.load(open('/scratch/jjyeung/orch_n30/swarm_an/work/pilot_key/key_k1.json'))
caps = {}
for kq, k in key.items(): caps[k['capture']] = kq.split('/')[0]
T = {}
for cap, alias in caps.items():
    ds, sc = cap.split('/'); T[tok({'scannetpp': 'scannetppv2'}.get(ds, ds), sc)] = (cap, alias)
print(len(T), 'tokens', list(T.items())[:2])
db = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite'
c = sqlite3.connect('file:' + db + '?mode=ro', uri=True)
n = c.execute('select max(i) from rows').fetchone()[0]; print('max i', n)
rx = re.compile(r'"scene":"(v[0-9a-f]{12})"'); rc = re.compile(r'"category":"([^"]+)"'); rp = re.compile(r'"pool":"?([^",}]+)')
hits = []; fam = collections.Counter(); t0 = time.time(); STEP = 4000; seen = 0
out = open('/tmp/v7_k1train_rows.jsonl', 'w')
for a in range(0, n + 1, STEP):
    for i, row in c.execute('select i, row from rows where i >= ? and i < ? limit ?', (a, a + STEP, STEP)):
        seen += 1; m = rx.search(row)
        if m and m.group(1) in T:
            cat = rc.search(row); fam[cat.group(1) if cat else None] += 1
            out.write(json.dumps(dict(i=i, scene=m.group(1), capture=T[m.group(1)][0], alias=T[m.group(1)][1], category=cat.group(1) if cat else None)) + '\n')
out.close()
print('rows seen', seen, 'seconds %.0f' % (time.time() - t0), 'hits', sum(fam.values())); print(dict(fam))

"""Admission packet for rows_a2's review path. Usage: packet.py ROWS_DIR PACKET_DIR
Writes PACKET_DIR/rows.sqlite (schema of the D0 v5 VQA store: rows(i, row, target='{}'), families in a fixed order),
the four family JSONL copies, MANIFEST.json (hashes, counts, rasters used, gate settings, checks) and refuses to
overwrite an existing packet."""
import sys, os, json, sqlite3, hashlib, shutil, collections
D, P = sys.argv[1], sys.argv[2]
os.makedirs(P)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
FAM = ('count_single', 'count_total', 'appearance', 'first_seen')
chk = json.load(open(os.path.join(D, 'CHECK.json'))); kp = json.load(open(os.path.join(D, 'KIT_PROOF.json')))
gen = json.load(open(os.path.join(D, 'GEN_MANIFEST.json')))
assert chk['verdict'] == 'PASS' and kp['status'] == 'PASS'
con = sqlite3.connect(os.path.join(P, 'rows.sqlite')); con.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT NOT NULL,target TEXT NOT NULL)')
i = 0; counts = {}; rasters = {}; qids = set()
for f in FAM:
    src = os.path.join(D, f + '.jsonl'); assert sha(src) == chk['files'][f] == gen['families'][f]['sha256']
    shutil.copyfile(src, os.path.join(P, f + '.jsonl')); c = collections.Counter()
    for line in open(src):
        r = json.loads(line); assert r['qid'] not in qids; qids.add(r['qid'])
        con.execute('INSERT INTO rows VALUES (?,?,?)', (i, json.dumps(r), '{}')); i += 1
        c[r['dataset']] += 1; rasters[r['provenance']['raster']] = r['provenance']['raster_sha256']
    counts[f] = dict(rows=sum(c.values()), by_dataset=dict(c), first_i=i - sum(c.values()), last_i=i - 1)
con.commit(); con.close()
man = dict(schema='b12-cntapp-packet-v1', database=dict(path=os.path.join(P, 'rows.sqlite'), sha256=sha(os.path.join(P, 'rows.sqlite')), rows=i),
           families={f: dict(counts[f], path=os.path.join(P, f + '.jsonl'), sha256=chk['files'][f]) for f in FAM},
           generator_sha256=gen['generator_sha256'], gtvis_sha256=gen['gtvis_sha256'], validator_sha256=chk['validator_sha256'],
           raster_roots=gen['raster_roots'], rasters=dict(sorted(rasters.items())), generation_stats=gen['stats'],
           check=dict(verdict=chk['verdict'], families={f: {k: v for k, v in chk['families'][f].items() if k != 'answer_hist'} for f in FAM}),
           answer_hist={f: chk['families'][f]['answer_hist'] for f in FAM}, kit_proof=dict(status=kp['status'], config=kp['config'], layout=kp['layout_settings']))
json.dump(man, open(os.path.join(P, 'MANIFEST.json'), 'w'), indent=1)
print(json.dumps({f: counts[f]['rows'] for f in FAM}), man['database']['sha256'])

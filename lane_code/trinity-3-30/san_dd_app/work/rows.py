"""Sample store-v7 appearance-order and first-seen rows by primary key (read-only, in memory). Lane san_dd_app."""
import json, random, sqlite3, re
DB = 'file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro'
RNG = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'
REC = ['/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json', '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json']
def removed():
    d = {}
    for f in REC:
        for l in open(f):
            l = l.strip()
            if l:
                r = json.loads(l); d[r.get('row_key')] = r.get('reason')
    return d
def ids(qtype):
    out = []
    for a, b in json.load(open(RNG))['families'][qtype]: out.extend(range(a, b + 1))
    return out
def fetch(idx):
    con = sqlite3.connect(DB, uri=True); out = []
    for k in range(0, len(idx), 200):
        ch = idx[k:k + 200]
        q = 'select i,row from rows where i in (%s)' % ','.join(str(int(x)) for x in ch)
        out.extend((i, json.loads(r)) for i, r in con.execute(q))
    con.close(); return out
def sample(qtype, n, seed=0):
    I = ids(qtype); return fetch(sorted(random.Random(seed).sample(I, min(n, len(I))))), len(I)
